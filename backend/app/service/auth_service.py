import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.asaas import customers as asaas_customers
from app.integrations.asaas.exceptions import AsaasAPIError
from app.models.usuario import Usuario
from app.repositories import usuario_repo
from app.schemas.usuario import CadastroRequest, LoginRequest


def _hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha[:72].encode(), bcrypt.gensalt()).decode()


def _verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha[:72].encode(), senha_hash.encode())


def _gerar_token(usuario_id: str, auth_time: int | None = None) -> str:
    agora = datetime.now(timezone.utc)
    expiracao = agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": usuario_id,
        "exp": expiracao,
        "iat": agora,
        # Momento do login original (epoch). Preservado pelas renovações para
        # impor o teto absoluto de sessão (SESSION_MAX_HOURS).
        "auth_time": auth_time if auth_time is not None else int(agora.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def renovar_token(token_atual: str) -> str:
    """Renovação deslizante do access token, preservando o `auth_time`.

    Exige um token atual ainda VÁLIDO e a sessão dentro do teto absoluto
    (SESSION_MAX_HOURS desde o login original) — sem refresh token separado.

    Decisão de proporcionalidade (11/06/2026): com o access token guardado em
    localStorage no frontend, um refresh token rotativo no mesmo storage não
    mudaria o perfil real de ameaça (um XSS captura ambos) e custaria tabela,
    rotação e revogação. O teto absoluto limita o deslizamento de um token
    roubado. Endurecimento futuro, se o projeto sair do escopo acadêmico:
    refresh token rotativo em cookie httpOnly + denylist.
    """
    credencial_invalida = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
    )
    try:
        payload = jwt.decode(
            token_atual, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        raise credencial_invalida

    # Tokens antigos (sem auth_time/iat) não são renováveis — força novo login.
    auth_time = int(payload.get("auth_time") or payload.get("iat") or 0)
    if auth_time <= 0 or not payload.get("sub"):
        raise credencial_invalida

    idade_sessao = datetime.now(timezone.utc).timestamp() - auth_time
    if idade_sessao > settings.SESSION_MAX_HOURS * 3600:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
        )

    return _gerar_token(payload["sub"], auth_time=auth_time)


async def cadastrar(db: AsyncSession, data: CadastroRequest) -> Usuario:
    if await usuario_repo.get_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    if await usuario_repo.get_by_cpf_cnpj(db, data.cpf_cnpj):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF/CNPJ já cadastrado.",
        )

    usuario_id = uuid.uuid4()
    try:
        customer = await asaas_customers.create_customer(
            nome=data.nome,
            cpf_cnpj=data.cpf_cnpj,
            email=data.email,
            celular=data.celular,
            usuario_id=usuario_id,
        )
    except AsaasAPIError as exc:
        # 4xx do Asaas significa que ele rejeitou os dados (CPF/CNPJ, e-mail, etc.)
        # — devolvemos 422 com a mensagem dele para o cliente corrigir e tentar de novo.
        # 5xx significa indisponibilidade do gateway: respondemos 502 genérico.
        if exc.is_client_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.user_message,
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gateway de pagamento indisponível. Tente novamente em instantes.",
        )

    return await usuario_repo.create(
        db,
        id=usuario_id,
        nome=data.nome,
        celular=data.celular,
        email=data.email,
        cpf_cnpj=data.cpf_cnpj,
        senha_hash=_hash_senha(data.senha),
        perfil=data.perfil,
        asaas_customer_id=customer["id"],
    )


async def login(db: AsyncSession, data: LoginRequest) -> tuple[str, Usuario]:
    usuario = await usuario_repo.get_by_email(db, data.email)

    if not usuario or not _verificar_senha(data.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )

    token = _gerar_token(str(usuario.id))
    return token, usuario
