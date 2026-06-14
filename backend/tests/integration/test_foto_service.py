"""Testes do UC08 — Galeria de Fotos (v1 grátis).

O storage do Supabase é mockado no namespace de `foto_service` (nos testes
`SUPABASE_*` fica sem valor, então a instância real é None). Validamos ownership,
tipo, tamanho, listagem e exclusão.
"""

import io
import uuid

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers
from unittest.mock import AsyncMock, MagicMock

from app.models.evento import StatusEvento
from app.models.usuario import PerfilUsuario
from app.repositories import foto_repo
from app.service import foto_service


@pytest.fixture
def mock_storage(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Substitui supabase_storage no foto_service por um mock funcional."""
    storage = MagicMock()
    storage.upload_foto_evento = AsyncMock(side_effect=lambda *a, **k: a[1])
    storage.criar_signed_url = MagicMock(return_value="https://signed.test/foto?token=x")
    storage.remover_foto = MagicMock(return_value=None)
    monkeypatch.setattr(foto_service, "supabase_storage", storage)
    return storage


def _upload(content_type: str = "image/jpeg", size: int = 1024) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(b"x" * size),
        filename="foto.jpg",
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_publicar_ok(db_session, organizador, criar_evento, mock_storage):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)

    fotos = await foto_service.publicar(
        db_session, organizador, evento.id, [_upload(), _upload()]
    )

    assert len(fotos) == 2
    assert all(f.url_original.startswith("https://signed.test/") for f in fotos)
    assert mock_storage.upload_foto_evento.await_count == 2
    persistidas = await foto_repo.list_by_evento(db_session, evento.id)
    assert len(persistidas) == 2
    assert all(float(p.preco) == 0 for p in persistidas)


@pytest.mark.asyncio
async def test_publicar_nao_dono_403(
    db_session, organizador, criar_evento, criar_usuario, mock_storage
):
    evento = await criar_evento(organizador)
    outro = await criar_usuario(
        perfil=PerfilUsuario.ORGANIZADOR, email="outro@test.com", cpf_cnpj="11222333000181"
    )

    with pytest.raises(HTTPException) as exc:
        await foto_service.publicar(db_session, outro, evento.id, [_upload()])
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_publicar_tipo_invalido_422(
    db_session, organizador, criar_evento, mock_storage
):
    evento = await criar_evento(organizador)

    with pytest.raises(HTTPException) as exc:
        await foto_service.publicar(
            db_session, organizador, evento.id, [_upload(content_type="application/pdf")]
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_publicar_tamanho_excedido_413(
    db_session, organizador, criar_evento, mock_storage
):
    evento = await criar_evento(organizador)
    grande = _upload(size=11 * 1024 * 1024)  # > MAX_FOTO_SIZE_MB (10)

    with pytest.raises(HTTPException) as exc:
        await foto_service.publicar(db_session, organizador, evento.id, [grande])
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_listar_por_evento(db_session, organizador, criar_evento, mock_storage):
    evento = await criar_evento(organizador)
    await foto_service.publicar(db_session, organizador, evento.id, [_upload()])

    fotos = await foto_service.listar_por_evento(db_session, evento.id)
    assert len(fotos) == 1
    assert fotos[0].evento_id == evento.id


@pytest.mark.asyncio
async def test_excluir_remove_e_valida_ownership(
    db_session, organizador, criar_evento, criar_usuario, mock_storage
):
    evento = await criar_evento(organizador)
    [foto] = await foto_service.publicar(db_session, organizador, evento.id, [_upload()])

    # Não-dono não exclui
    outro = await criar_usuario(
        perfil=PerfilUsuario.ORGANIZADOR, email="outro@test.com", cpf_cnpj="11222333000181"
    )
    with pytest.raises(HTTPException) as exc:
        await foto_service.excluir(db_session, outro, foto.id)
    assert exc.value.status_code == 403

    # Dono exclui
    await foto_service.excluir(db_session, organizador, foto.id)
    assert await foto_repo.get_by_id(db_session, foto.id) is None
    mock_storage.remover_foto.assert_called_once()


@pytest.mark.asyncio
async def test_excluir_inexistente_404(db_session, organizador, mock_storage):
    with pytest.raises(HTTPException) as exc:
        await foto_service.excluir(db_session, organizador, uuid.uuid4())
    assert exc.value.status_code == 404
