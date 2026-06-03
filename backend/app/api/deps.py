import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.db.session import get_db
from app.models.usuario import PerfilUsuario, Usuario
from app.repositories import usuario_repo
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer()

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> Usuario:
    credencial_invalida = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise credencial_invalida
        usuario_uuid = uuid.UUID(usuario_id)
    except (jwt.PyJWTError, ValueError):
        raise credencial_invalida

    usuario = await usuario_repo.get_by_id(db, usuario_uuid)
    if not usuario or not usuario.ativo:
        raise credencial_invalida

    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


async def get_current_organizador(usuario: CurrentUser) -> Usuario:
    if usuario.perfil != PerfilUsuario.ORGANIZADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas organizadores podem realizar esta operação.",
        )
    return usuario


OrganizadorUser = Annotated[Usuario, Depends(get_current_organizador)]


async def get_current_participante(usuario: CurrentUser) -> Usuario:
    if usuario.perfil != PerfilUsuario.PARTICIPANTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas participantes podem realizar esta operação.",
        )
    return usuario


ParticipanteUser = Annotated[Usuario, Depends(get_current_participante)]
