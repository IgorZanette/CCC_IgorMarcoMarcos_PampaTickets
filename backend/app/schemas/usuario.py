import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validators import validar_cpf_cnpj
from app.models.usuario import PerfilUsuario


class CadastroRequest(BaseModel):
    nome: str = Field(
        ..., min_length=2, max_length=255, examples=["Marco Antônio Santolin"]
    )
    email: EmailStr = Field(..., examples=["marco.antonio@santolin.com.br"])
    cpf_cnpj: str = Field(..., examples=["029.612.990-98"])
    celular: str = Field(..., examples=["54999407969"])
    senha: str = Field(..., min_length=8, max_length=72, examples=["Marco123"])
    perfil: PerfilUsuario = Field(..., examples=["ORGANIZADOR"])

    @field_validator("cpf_cnpj")
    @classmethod
    def normalizar_cpf_cnpj(cls, v: str) -> str:
        return validar_cpf_cnpj(v)

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, v: str) -> str:
        numero = re.sub(r"\D", "", v)
        if not re.fullmatch(r"[1-9]{2}9\d{8}", numero):
            raise ValueError(
                "Celular inválido. Informe DDD + 9 dígitos (ex: 54999407969)."
            )
        return numero

    @field_validator("senha")
    @classmethod
    def validar_forca_senha(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("A senha deve conter ao menos uma letra e um número.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["marco.antonio@santolin.com.br"])
    senha: str = Field(..., examples=["Marco123"])


class UsuarioResponse(BaseModel):
    id: uuid.UUID = Field(..., examples=["550e8400-e29b-41d4-a716-446655440000"])
    nome: str = Field(..., examples=["Marco Antônio Santolin"])
    email: str = Field(..., examples=["marco.antonio@santolin.com.br"])
    cpf_cnpj: str = Field(..., examples=["029.612.990-98"])
    celular: str = Field(..., examples=["54999407969"])
    perfil: PerfilUsuario = Field(..., examples=["ORGANIZADOR"])
    ativo: bool = Field(..., examples=[True])
    criado_em: datetime = Field(..., examples=["2026-04-04T10:00:00"])

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field(default="bearer", examples=["bearer"])
    usuario: UsuarioResponse
