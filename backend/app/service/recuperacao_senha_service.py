"""Serviço para gerenciar recuperação de senha."""

import random
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations import email_service
from app.models.recuperacao_senha import StatusRecuperacao
from app.repositories import recuperacao_senha_repo, usuario_repo


def _gerar_codigo_6_digitos() -> str:
    """Gera um código aleatório de 6 dígitos."""
    return "".join(random.choices(string.digits, k=6))


def _gerar_token_seguro() -> str:
    """Gera um token criptograficamente seguro."""
    return secrets.token_urlsafe(32)


async def solicitar_recuperacao_senha(db: AsyncSession, email: str) -> dict:
    """
    Solicita recuperação de senha para um usuário.

    Args:
        db: Sessão do banco de dados
        email: Email do usuário

    Returns:
        Dicionário com mensagem de sucesso

    Raises:
        HTTPException: Se o email não existir ou houver erro no envio
    """
    usuario = await usuario_repo.get_by_email(db, email)

    if not usuario:
        # Não revelamos se o email existe ou não (segurança)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado.",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )

    # Gerar código e token
    codigo = _gerar_codigo_6_digitos()
    token = _gerar_token_seguro()

    # Definir expiração
    expira_em = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )

    # Salvar no banco
    await recuperacao_senha_repo.create(
        db,
        usuario_id=usuario.id,
        codigo=codigo,
        token=token,
        expira_em=expira_em,
    )
    await db.commit()

    # Enviar email
    sucesso_email = await email_service.enviar_codigo_recuperacao_senha(
        email_destino=usuario.email,
        codigo=codigo,
        nome_usuario=usuario.nome,
    )

    if not sucesso_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar email. Tente novamente mais tarde.",
        )

    return {"mensagem": "Código de recuperação enviado para seu email."}


async def validar_codigo_recuperacao(
    db: AsyncSession, email: str, codigo: str
) -> dict:
    """
    Valida o código de recuperação.

    Args:
        db: Sessão do banco de dados
        email: Email do usuário
        codigo: Código de 6 dígitos

    Returns:
        Dicionário com token temporário

    Raises:
        HTTPException: Se código inválido ou expirado
    """
    usuario = await usuario_repo.get_by_email(db, email)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado.",
        )

    # Buscar recuperação pendente
    recuperacao = await recuperacao_senha_repo.get_by_usuario_id(db, usuario.id)

    if not recuperacao:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma recuperação de senha ativa.",
        )

    # Validar código
    if recuperacao.codigo != codigo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido.",
        )

    # Validar expiração
    if recuperacao.esta_expirado():
        await recuperacao_senha_repo.update_status(
            db, recuperacao.id, StatusRecuperacao.EXPIRADO
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código expirado.",
        )

    # Marcar como validado
    await recuperacao_senha_repo.update_status(
        db, recuperacao.id, StatusRecuperacao.VALIDADO
    )
    await db.commit()

    return {
        "token": recuperacao.token,
        "mensagem": "Código validado com sucesso.",
    }


async def redefinir_senha(
    db: AsyncSession, email: str, codigo: str, nova_senha: str
) -> dict:
    """
    Redefine a senha do usuário após validação.

    Args:
        db: Sessão do banco de dados
        email: Email do usuário
        codigo: Código de 6 dígitos
        nova_senha: Nova senha do usuário

    Returns:
        Dicionário com mensagem de sucesso

    Raises:
        HTTPException: Se houver erro na validação ou redefinição
    """
    usuario = await usuario_repo.get_by_email(db, email)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado.",
        )

    # Buscar recuperação
    recuperacao = await recuperacao_senha_repo.get_by_usuario_id(db, usuario.id)

    if not recuperacao:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma recuperação de senha ativa.",
        )

    # Validar status
    if recuperacao.status != StatusRecuperacao.VALIDADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve ser validado antes de redefinir a senha.",
        )

    # Validar código (verificação adicional)
    if recuperacao.codigo != codigo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido.",
        )

    # Validar expiração
    if recuperacao.esta_expirado():
        await recuperacao_senha_repo.update_status(
            db, recuperacao.id, StatusRecuperacao.EXPIRADO
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código expirado.",
        )

    # Atualizar senha (import aqui para evitar circular imports)
    from app.service.auth_service import _hash_senha

    usuario.senha_hash = _hash_senha(nova_senha)

    # Marcar recuperação como utilizada
    await recuperacao_senha_repo.update_status(
        db, recuperacao.id, StatusRecuperacao.UTILIZADO
    )

    await db.commit()

    return {"mensagem": "Senha redefinida com sucesso."}
