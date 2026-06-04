from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, DbDep
from app.core.rate_limit import limiter
from app.schemas.usuario import (
    CadastroRequest,
    LoginRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/cadastro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("20/minute")
async def cadastro(request: Request, data: CadastroRequest, db: DbDep):
    usuario = await auth_service.cadastrar(db, data)
    return usuario


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(request: Request, data: LoginRequest, db: DbDep):
    token, usuario = await auth_service.login(db, data)
    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioResponse)
async def me(current_user: CurrentUser):
    return current_user
