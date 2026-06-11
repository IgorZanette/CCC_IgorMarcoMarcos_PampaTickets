from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, DbDep
from app.core.rate_limit import limiter
from app.schemas.usuario import (
    CadastroRequest,
    CodigoValidadoResponse,
    LoginRequest,
    RecuperacaoSenhaRequest,
    RecuperacaoSenhaResponse,
    RedefinirSenhaRequest,
    TokenResponse,
    UsuarioResponse,
    ValidarCodigoRecuperacaoRequest,
)
from app.service import auth_service, recuperacao_senha_service

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


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(request: Request, current_user: CurrentUser):
    """Renova o access token (sliding) enquanto a sessão estiver dentro do
    teto absoluto. O CurrentUser já garante token válido e conta ativa."""
    auth = request.headers.get("Authorization", "")
    token_atual = auth.removeprefix("Bearer ").strip()
    novo_token = auth_service.renovar_token(token_atual)
    return TokenResponse(access_token=novo_token, usuario=current_user)


@router.post(
    "/forgot-password",
    response_model=RecuperacaoSenhaResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def solicitar_recuperacao_senha(
    request: Request, data: RecuperacaoSenhaRequest, db: DbDep
):
    """
    Solicita código de recuperação de senha para o email informado.
    O código será enviado por email.
    """
    resultado = await recuperacao_senha_service.solicitar_recuperacao_senha(
        db, data.email
    )
    return resultado


@router.post(
    "/validate-reset-code",
    response_model=CodigoValidadoResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def validar_codigo_recuperacao(
    request: Request, data: ValidarCodigoRecuperacaoRequest, db: DbDep
):
    """
    Valida o código de 6 dígitos enviado por email.
    Retorna um token temporário para redefinição de senha.
    """
    resultado = await recuperacao_senha_service.validar_codigo_recuperacao(
        db, data.email, data.codigo
    )
    return resultado


@router.post(
    "/reset-password",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def redefinir_senha(
    request: Request, data: RedefinirSenhaRequest, db: DbDep
):
    """
    Redefine a senha do usuário após validação do código.
    """
    resultado = await recuperacao_senha_service.redefinir_senha(
        db, data.email, data.codigo, data.nova_senha
    )
    return resultado

