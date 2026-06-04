"""Testes unitários dos helpers de auth (hash de senha e geração de JWT)."""

from datetime import datetime, timezone

import jwt

from app.core.config import settings
from app.service import auth_service


def test_hash_difere_da_senha_e_verifica():
    senha = "minha-senha-secreta"
    hashed = auth_service._hash_senha(senha)
    assert hashed != senha
    assert auth_service._verificar_senha(senha, hashed) is True


def test_verificacao_falha_com_senha_errada():
    hashed = auth_service._hash_senha("correta")
    assert auth_service._verificar_senha("errada", hashed) is False


def test_token_contem_sub_e_exp_futuro():
    token = auth_service._gerar_token("usuario-123")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "usuario-123"
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()
