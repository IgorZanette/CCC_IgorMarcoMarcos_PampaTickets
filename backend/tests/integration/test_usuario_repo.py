"""Testes de integração do repositório de usuários e do validador do model."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.usuario import PerfilUsuario, Usuario
from app.repositories import usuario_repo
from app.service import auth_service


async def _criar(db, *, email, cpf_cnpj):
    return await usuario_repo.create(
        db,
        nome="Maria Teste",
        celular="54999407969",
        cpf_cnpj=cpf_cnpj,
        email=email,
        senha_hash=auth_service._hash_senha("senha"),
        perfil=PerfilUsuario.PARTICIPANTE,
    )


async def test_create_e_getters(db_session):
    usuario = await _criar(db_session, email="maria@test.com", cpf_cnpj="52998224725")
    assert usuario.id is not None

    por_email = await usuario_repo.get_by_email(db_session, "maria@test.com")
    assert por_email is not None
    assert por_email.id == usuario.id

    por_id = await usuario_repo.get_by_id(db_session, usuario.id)
    assert por_id is not None
    assert por_id.email == "maria@test.com"

    por_doc = await usuario_repo.get_by_cpf_cnpj(db_session, "52998224725")
    assert por_doc is not None
    assert por_doc.id == usuario.id


async def test_get_by_email_inexistente(db_session):
    assert await usuario_repo.get_by_email(db_session, "ninguem@test.com") is None


async def test_email_duplicado_levanta_integrity_error(db_session):
    await _criar(db_session, email="dup@test.com", cpf_cnpj="52998224725")
    with pytest.raises(IntegrityError):
        await _criar(db_session, email="dup@test.com", cpf_cnpj="11222333000181")
    await db_session.rollback()


def test_model_rejeita_cpf_invalido():
    with pytest.raises(ValueError):
        Usuario(
            nome="X",
            email="x@test.com",
            cpf_cnpj="11111111111",
            celular="54999407969",
            senha_hash="hash",
            perfil=PerfilUsuario.PARTICIPANTE,
        )
