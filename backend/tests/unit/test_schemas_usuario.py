"""Testes unitários de validação do schema CadastroRequest."""

import pytest
from pydantic import ValidationError

from app.models.usuario import PerfilUsuario
from app.schemas.usuario import CadastroRequest


def _payload(**overrides):
    base = {
        "nome": "Fulano de Tal",
        "email": "fulano@test.com",
        "cpf_cnpj": "529.982.247-25",
        "celular": "54999407969",
        "senha": "senha-forte-123",
        "perfil": PerfilUsuario.ORGANIZADOR,
    }
    base.update(overrides)
    return base


def test_cadastro_valido_normaliza_documento():
    req = CadastroRequest(**_payload())
    assert req.cpf_cnpj == "52998224725"
    assert req.celular == "54999407969"


def test_cpf_invalido_rejeitado():
    with pytest.raises(ValidationError):
        CadastroRequest(**_payload(cpf_cnpj="111.111.111-11"))


def test_celular_invalido_rejeitado():
    with pytest.raises(ValidationError):
        CadastroRequest(**_payload(celular="123"))


def test_senha_curta_rejeitada():
    with pytest.raises(ValidationError):
        CadastroRequest(**_payload(senha="curta"))


def test_senha_sem_numero_rejeitada():
    with pytest.raises(ValidationError):
        CadastroRequest(**_payload(senha="apenasletras"))


def test_perfil_invalido_rejeitado():
    with pytest.raises(ValidationError):
        CadastroRequest(**_payload(perfil="ADMIN"))
