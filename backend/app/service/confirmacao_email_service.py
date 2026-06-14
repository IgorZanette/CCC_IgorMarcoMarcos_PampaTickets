"""Serviço para gerenciar confirmação de email no cadastro.

Segue o mesmo padrão de endurecimento de recuperacao_senha_service:
- Anti-enumeração: resposta idêntica para email existente ou não.
- Anti-brute-force: código invalidado após MAX_TENTATIVAS_CODIGO erros.
- Código nunca em claro: HMAC-SHA256 com SECRET_KEY como pepper,
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
from app.models.confirmacao_email import ConfirmacaoEmail, StatusConfirmacaoEmail
from app.repositories import confirmacao_email_repo, usuario_repo

MAX_TENTATIVAS_CODIGO = 5
EXPIRACAO_HORAS = 24

_MSG_SOLICITACAO = (
    "Se o e-mail estiver cadastrado e não confirmado, você receberá um código de confirmação."
)
_MSG_CODIGO_INVALIDO = "Código inválido ou expirado."
_MSG_LOCKOUT = "Muitas tentativas incorretas. Solicite um novo código."


def _gerar_codigo_6_digitos() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


def _gerar_token_seguro() -> str:
    return secrets.token_urlsafe(32)


def _hash_codigo(codigo: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256
    ).hexdigest()


def _codigo_confere(confirmacao: ConfirmacaoEmail, codigo: str) -> bool:
    return hmac.compare_digest(confirmacao.codigo_hash, _hash_codigo(codigo))


def _erro_codigo_invalido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=_MSG_CODIGO_INVALIDO,
    )


async def _enviar_codigo(email: str, codigo: str, nome: str) -> None:
    """Envio em background — falha é logada, nunca exposta na resposta."""
    try:
        sucesso = await email_service.enviar_confirmacao_email(
            email_destino=email,
            codigo=codigo,
            nome_usuario=nome,
        )
        if not sucesso:
            logger.error("Falha ao enviar e-mail de confirmação de conta")
    except Exception:
        logger.exception("Erro ao enviar e-mail de confirmação de conta")


async def _registrar_tentativa_errada(
    db: AsyncSession, confirmacao: ConfirmacaoEmail
) -> None:
    tentativas = await confirmacao_email_repo.incrementar_tentativas(db, confirmacao.id)
    estourou = tentativas >= MAX_TENTATIVAS_CODIGO
    if estourou:
        await confirmacao_email_repo.update_status(
            db, confirmacao.id, StatusConfirmacaoEmail.EXPIRADO
        )
    await db.commit()
    if estourou:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_MSG_LOCKOUT,
        )
    raise _erro_codigo_invalido()


async def solicitar_confirmacao_email(
    db: AsyncSession,
    usuario_id,
    email_destino: str,
    nome: str,
    background_tasks: BackgroundTasks,
) -> None:
    """Cria código de confirmação e agenda envio de email."""
    codigo = _gerar_codigo_6_digitos()
    token = _gerar_token_seguro()
    expira_em = datetime.now(timezone.utc) + timedelta(hours=EXPIRACAO_HORAS)

    await confirmacao_email_repo.invalidar_pendentes(db, usuario_id)
    await confirmacao_email_repo.create(
        db,
        usuario_id=usuario_id,
        codigo_hash=_hash_codigo(codigo),
        token=token,
        expira_em=expira_em,
    )
    await db.commit()

    background_tasks.add_task(
        _enviar_codigo, email=email_destino, codigo=codigo, nome=nome
    )


async def confirmar_email(db: AsyncSession, email: str, codigo: str) -> dict:
    """Valida o código de 6 dígitos e marca o email do usuário como verificado."""
    usuario = await usuario_repo.get_by_email(db, email)
    if usuario is None:
        raise _erro_codigo_invalido()

    if usuario.email_verificado:
        return {"mensagem": "E-mail já confirmado."}

    confirmacao = await confirmacao_email_repo.get_pendente_por_usuario(db, usuario.id)
    if confirmacao is None:
        raise _erro_codigo_invalido()

    if confirmacao.esta_expirado():
        await confirmacao_email_repo.update_status(
            db, confirmacao.id, StatusConfirmacaoEmail.EXPIRADO
        )
        await db.commit()
        raise _erro_codigo_invalido()

    if not _codigo_confere(confirmacao, codigo):
        await _registrar_tentativa_errada(db, confirmacao)

    await confirmacao_email_repo.update_status(
        db, confirmacao.id, StatusConfirmacaoEmail.UTILIZADO
    )
    usuario.email_verificado = True
    await db.commit()

    return {"mensagem": "E-mail confirmado com sucesso. Você já pode fazer login."}


async def reenviar_confirmacao(
    db: AsyncSession, email: str, background_tasks: BackgroundTasks
) -> dict:
    """Reenvia código de confirmação.

    Anti-enumeração: resposta idêntica independente de o email existir ou não.
    """
    usuario = await usuario_repo.get_by_email(db, email)

    if usuario is None or not usuario.ativo or usuario.email_verificado:
        logger.info("Reenvio de confirmação solicitado para conta não elegível")
        return {"mensagem": _MSG_SOLICITACAO}

    await solicitar_confirmacao_email(
        db,
        usuario_id=usuario.id,
        email_destino=usuario.email,
        nome=usuario.nome,
        background_tasks=background_tasks,
    )

    return {"mensagem": _MSG_SOLICITACAO}
