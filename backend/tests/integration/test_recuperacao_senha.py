"""Testes do fluxo endurecido de recuperação de senha (anti-enumeração,
anti-brute-force, código hasheado com comparação constant-time)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select

from app.models.recuperacao_senha import RecuperacaoSenha, StatusRecuperacao
from app.service import auth_service, recuperacao_senha_service
from app.service.recuperacao_senha_service import (
    MAX_TENTATIVAS_CODIGO,
    _hash_codigo,
)


@pytest.fixture
def email_mock(monkeypatch) -> AsyncMock:
    """Intercepta o envio de e-mail — captura o código em claro enviado."""
    mock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        recuperacao_senha_service.email_service,
        "enviar_codigo_recuperacao_senha",
        mock,
    )
    return mock


async def _solicitar(db, email: str, email_mock: AsyncMock) -> str:
    """Solicita a recuperação, executa o background task e devolve o código."""
    chamadas_antes = email_mock.await_count
    bg = BackgroundTasks()
    resultado = await recuperacao_senha_service.solicitar_recuperacao_senha(
        db, email, bg
    )
    assert "Se o e-mail estiver cadastrado" in resultado["mensagem"]
    await bg()  # executa os tasks como o Starlette faria após a resposta
    assert email_mock.await_count == chamadas_antes + 1
    return email_mock.call_args.kwargs["codigo"]


async def _recuperacao_de(db, usuario_id) -> RecuperacaoSenha:
    result = await db.execute(
        select(RecuperacaoSenha)
        .where(RecuperacaoSenha.usuario_id == usuario_id)
        .order_by(RecuperacaoSenha.criado_em.desc())
    )
    return result.scalars().first()


async def test_solicitar_resposta_generica_para_email_inexistente(
    db_session, email_mock
):
    bg = BackgroundTasks()
    resultado = await recuperacao_senha_service.solicitar_recuperacao_senha(
        db_session, "nao-existe@test.com", bg
    )
    await bg()
    # Mesma mensagem do caso de sucesso; nenhum e-mail enviado, nada criado.
    assert "Se o e-mail estiver cadastrado" in resultado["mensagem"]
    email_mock.assert_not_awaited()


async def test_solicitar_armazena_hash_e_nao_o_codigo(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)
    rec = await _recuperacao_de(db_session, participante.id)
    assert rec is not None
    assert rec.status == StatusRecuperacao.PENDENTE
    # O código em claro não está no banco — só o HMAC dele.
    assert rec.codigo_hash != codigo
    assert len(rec.codigo_hash) == 64
    assert rec.codigo_hash == _hash_codigo(codigo)


async def test_validar_email_inexistente_devolve_mesmo_erro_generico(db_session):
    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.validar_codigo_recuperacao(
            db_session, "nao-existe@test.com", "123456"
        )
    # 400 genérico — não 404 "Email não encontrado" (anti-enumeração).
    assert exc.value.status_code == 400
    assert exc.value.detail == "Código inválido ou expirado."


async def test_brute_force_bloqueia_e_invalida_o_codigo(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)
    errado = "000000" if codigo != "000000" else "111111"

    # As tentativas antes do limite devolvem o erro genérico.
    for _ in range(MAX_TENTATIVAS_CODIGO - 1):
        with pytest.raises(HTTPException) as exc:
            await recuperacao_senha_service.validar_codigo_recuperacao(
                db_session, participante.email, errado
            )
        assert exc.value.detail == "Código inválido ou expirado."

    # A tentativa que estoura o limite avisa o lockout e invalida o código.
    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.validar_codigo_recuperacao(
            db_session, participante.email, errado
        )
    assert "Muitas tentativas" in exc.value.detail

    # Mesmo o código CORRETO não funciona mais — é preciso pedir outro.
    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.validar_codigo_recuperacao(
            db_session, participante.email, codigo
        )
    assert exc.value.status_code == 400

    rec = await _recuperacao_de(db_session, participante.id)
    assert rec.status == StatusRecuperacao.EXPIRADO
    assert rec.tentativas == MAX_TENTATIVAS_CODIGO


async def test_novo_pedido_invalida_codigo_anterior(
    db_session, participante, email_mock
):
    codigo1 = await _solicitar(db_session, participante.email, email_mock)
    codigo2 = await _solicitar(db_session, participante.email, email_mock)

    if codigo1 != codigo2:  # colisão de 1 em 10^6 não deve quebrar o teste
        with pytest.raises(HTTPException):
            await recuperacao_senha_service.validar_codigo_recuperacao(
                db_session, participante.email, codigo1
            )

    resultado = await recuperacao_senha_service.validar_codigo_recuperacao(
        db_session, participante.email, codigo2
    )
    assert resultado["token"]


async def test_codigo_expirado_devolve_erro_generico(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)
    rec = await _recuperacao_de(db_session, participante.id)
    rec.expira_em = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.validar_codigo_recuperacao(
            db_session, participante.email, codigo
        )
    assert exc.value.detail == "Código inválido ou expirado."
    rec = await _recuperacao_de(db_session, participante.id)
    assert rec.status == StatusRecuperacao.EXPIRADO


async def test_fluxo_completo_redefine_a_senha(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)

    validado = await recuperacao_senha_service.validar_codigo_recuperacao(
        db_session, participante.email, codigo
    )
    assert validado["token"]

    # O reset usa o TOKEN devolvido pela validação — não o código.
    resultado = await recuperacao_senha_service.redefinir_senha(
        db_session, participante.email, validado["token"], "NovaSenha123"
    )
    assert "redefinida" in resultado["mensagem"]

    await db_session.refresh(participante)
    assert auth_service._verificar_senha("NovaSenha123", participante.senha_hash)
    rec = await _recuperacao_de(db_session, participante.id)
    assert rec.status == StatusRecuperacao.UTILIZADO


async def test_redefinir_sem_validar_antes_erro_generico(
    db_session, participante, email_mock
):
    # Mesmo com o token correto, status PENDENTE (não validado) responde o
    # MESMO erro genérico — mensagem distinta seria oráculo de que existe
    # uma recuperação em andamento para o e-mail.
    await _solicitar(db_session, participante.email, email_mock)
    rec = await _recuperacao_de(db_session, participante.id)
    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.redefinir_senha(
            db_session, participante.email, rec.token, "NovaSenha123"
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Código inválido ou expirado."


async def test_redefinir_token_errado_erro_generico(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)
    await recuperacao_senha_service.validar_codigo_recuperacao(
        db_session, participante.email, codigo
    )
    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.redefinir_senha(
            db_session, participante.email, "token-forjado-qualquer", "NovaSenha123"
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Código inválido ou expirado."


async def test_redefinir_expirado_apos_validacao_erro_generico(
    db_session, participante, email_mock
):
    codigo = await _solicitar(db_session, participante.email, email_mock)
    validado = await recuperacao_senha_service.validar_codigo_recuperacao(
        db_session, participante.email, codigo
    )
    rec = await _recuperacao_de(db_session, participante.id)
    rec.expira_em = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await recuperacao_senha_service.redefinir_senha(
            db_session, participante.email, validado["token"], "NovaSenha123"
        )
    assert exc.value.detail == "Código inválido ou expirado."
    rec = await _recuperacao_de(db_session, participante.id)
    assert rec.status == StatusRecuperacao.EXPIRADO
