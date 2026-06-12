"""Serviço para gerenciar recuperação de senha.

Endurecimento (11/06/2026 — achados registrados no PR #2):
- Anti-enumeração: a resposta de solicitação é sempre a mesma, exista a conta
  ou não, e o e-mail é enviado em background (a latência do SMTP não denuncia
  a existência do cadastro). Validação/redefinição respondem o mesmo erro
  genérico para e-mail desconhecido e código errado.
- Anti-brute-force: tentativas erradas de código contam por recuperação; ao
  estourar MAX_TENTATIVAS_CODIGO o código é invalidado (rate limit por IP já
  existe nas rotas, mas não protege contra ataque distribuído).
- Código nunca em claro: armazenado como HMAC-SHA256 com a SECRET_KEY de
  pepper (hash puro de 6 dígitos é quebrável offline em milissegundos) e
  comparado em tempo constante (hmac.compare_digest).
"""

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations import email_service
from app.models.recuperacao_senha import RecuperacaoSenha, StatusRecuperacao
from app.repositories import recuperacao_senha_repo, usuario_repo

# 6 dígitos ≈ 10^6 combinações; com 5 tentativas a chance de adivinhar um
# código é 0,0005%. Estourou: o código é invalidado e é preciso pedir outro.
MAX_TENTATIVAS_CODIGO = 5

_MSG_SOLICITACAO = (
    "Se o e-mail estiver cadastrado, você receberá um código de recuperação."
)
_MSG_CODIGO_INVALIDO = "Código inválido ou expirado."
_MSG_LOCKOUT = "Muitas tentativas incorretas. Solicite um novo código."


def _gerar_codigo_6_digitos() -> str:
    """Gera um código aleatório de 6 dígitos usando CSPRNG (secrets)."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


def _gerar_token_seguro() -> str:
    """Gera um token criptograficamente seguro."""
    return secrets.token_urlsafe(32)


def _hash_codigo(codigo: str) -> str:
    """HMAC-SHA256 do código, com a SECRET_KEY como pepper."""
    return hmac.new(
        settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256
    ).hexdigest()


def _codigo_confere(recuperacao: RecuperacaoSenha, codigo: str) -> bool:
    """Comparação em tempo constante entre o hash armazenado e o código."""
    return hmac.compare_digest(recuperacao.codigo_hash, _hash_codigo(codigo))


def _erro_codigo_invalido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=_MSG_CODIGO_INVALIDO,
    )


async def _enviar_codigo(email: str, codigo: str, nome: str) -> None:
    """Envio em background — falha é logada, nunca exposta na resposta."""
    try:
        sucesso = await email_service.enviar_codigo_recuperacao_senha(
            email_destino=email,
            codigo=codigo,
            nome_usuario=nome,
        )
        if not sucesso:
            logger.error("Falha ao enviar e-mail de recuperação de senha")
    except Exception:
        logger.exception("Erro ao enviar e-mail de recuperação de senha")


async def _recuperacao_ativa(
    db: AsyncSession, email: str
) -> RecuperacaoSenha | None:
    """Recuperação ativa do e-mail — None para conta inexistente também,
    para que o chamador responda o mesmo erro genérico (anti-enumeração)."""
    usuario = await usuario_repo.get_by_email(db, email)
    if usuario is None:
        return None
    return await recuperacao_senha_repo.get_by_usuario_id(db, usuario.id)


async def _registrar_tentativa_errada(
    db: AsyncSession, recuperacao: RecuperacaoSenha
) -> None:
    """Conta a tentativa errada; ao estourar o limite, invalida o código.

    O incremento é um UPDATE atômico no banco (não read-modify-write em
    Python) — requisições paralelas com código errado não conseguem dividir
    a mesma contagem e ultrapassar o limite.
    """
    tentativas = await recuperacao_senha_repo.incrementar_tentativas(
        db, recuperacao.id
    )
    estourou = tentativas >= MAX_TENTATIVAS_CODIGO
    if estourou:
        await recuperacao_senha_repo.update_status(
            db, recuperacao.id, StatusRecuperacao.EXPIRADO
        )
    await db.commit()
    if estourou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_MSG_LOCKOUT,
        )
    raise _erro_codigo_invalido()


async def solicitar_recuperacao_senha(
    db: AsyncSession, email: str, background_tasks: BackgroundTasks
) -> dict:
    """Inicia a recuperação de senha.

    A resposta é idêntica para e-mail cadastrado, inexistente ou conta
    desativada — quem pergunta não descobre se a conta existe. O envio do
    e-mail vai para background para a latência do SMTP não servir de oráculo.
    """
    usuario = await usuario_repo.get_by_email(db, email)

    if usuario is None or not usuario.ativo:
        # Loga pelo request_id do middleware; sem e-mail no log (PII).
        logger.info("Recuperação de senha solicitada para conta não elegível")
        return {"mensagem": _MSG_SOLICITACAO}

    codigo = _gerar_codigo_6_digitos()
    token = _gerar_token_seguro()
    expira_em = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )

    # Um código válido por vez: novos pedidos invalidam os anteriores
    # (também zera qualquer contagem de tentativas em andamento).
    await recuperacao_senha_repo.invalidar_ativas(db, usuario.id)
    await recuperacao_senha_repo.create(
        db,
        usuario_id=usuario.id,
        codigo_hash=_hash_codigo(codigo),
        token=token,
        expira_em=expira_em,
    )
    await db.commit()

    background_tasks.add_task(
        _enviar_codigo, email=usuario.email, codigo=codigo, nome=usuario.nome
    )

    return {"mensagem": _MSG_SOLICITACAO}


async def validar_codigo_recuperacao(
    db: AsyncSession, email: str, codigo: str
) -> dict:
    """Valida o código de 6 dígitos e devolve o token de redefinição.

    Mesmo erro genérico para e-mail desconhecido, sem recuperação ativa,
    código expirado ou código errado. Tentativas erradas contam para o
    lockout do código.
    """
    recuperacao = await _recuperacao_ativa(db, email)
    if recuperacao is None:
        raise _erro_codigo_invalido()

    if recuperacao.esta_expirado():
        await recuperacao_senha_repo.update_status(
            db, recuperacao.id, StatusRecuperacao.EXPIRADO
        )
        await db.commit()
        raise _erro_codigo_invalido()

    if not _codigo_confere(recuperacao, codigo):
        await _registrar_tentativa_errada(db, recuperacao)

    await recuperacao_senha_repo.update_status(
        db, recuperacao.id, StatusRecuperacao.VALIDADO
    )
    await db.commit()

    return {
        "token": recuperacao.token,
        "mensagem": "Código validado com sucesso.",
    }


async def redefinir_senha(
    db: AsyncSession, email: str, token: str, nova_senha: str
) -> dict:
    """Redefine a senha usando o token devolvido pela validação do código.

    O token (256 bits, não adivinhável) é o que autoriza o reset — o código
    de 6 dígitos morre na etapa de validação e não volta a transitar pelo
    cliente. Todos os caminhos de falha respondem o MESMO erro genérico
    (e-mail desconhecido, sem recuperação ativa, status não validado, token
    errado, expirado): mensagens distintas funcionariam como oráculo de que
    existe uma recuperação em andamento para aquele e-mail.
    """
    recuperacao = await _recuperacao_ativa(db, email)
    if recuperacao is None:
        raise _erro_codigo_invalido()

    if recuperacao.status != StatusRecuperacao.VALIDADO:
        raise _erro_codigo_invalido()

    if recuperacao.esta_expirado():
        await recuperacao_senha_repo.update_status(
            db, recuperacao.id, StatusRecuperacao.EXPIRADO
        )
        await db.commit()
        raise _erro_codigo_invalido()

    if not hmac.compare_digest(recuperacao.token, token):
        raise _erro_codigo_invalido()

    usuario = await usuario_repo.get_by_email(db, email)
    if usuario is None:  # impossível após _recuperacao_ativa, mas defensivo
        raise _erro_codigo_invalido()

    # Import aqui para evitar import circular.
    from app.service.auth_service import _hash_senha

    usuario.senha_hash = _hash_senha(nova_senha)

    await recuperacao_senha_repo.update_status(
        db, recuperacao.id, StatusRecuperacao.UTILIZADO
    )
    await db.commit()

    return {"mensagem": "Senha redefinida com sucesso."}
