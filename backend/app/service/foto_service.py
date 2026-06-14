import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.supabase.supabase_storage import supabase_storage
from app.models.foto import FotoEvento
from app.models.usuario import Usuario
from app.repositories import evento_repo, foto_repo
from app.schemas.foto import FotoResponse

# Extensão do arquivo por content-type aceito (espelha ALLOWED_FOTO_TYPES).
_EXTENSAO_POR_TIPO = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


async def publicar(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
    files: list[UploadFile],
) -> list[FotoResponse]:
    """Publica uma ou mais fotos na galeria do evento (UC08, galeria grátis)."""
    evento = await _validar_ownership_evento(db, organizador, evento_id)

    if supabase_storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Armazenamento de fotos indisponível no momento.",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Envie pelo menos uma foto.",
        )

    max_bytes = settings.MAX_FOTO_SIZE_MB * 1024 * 1024
    publicadas: list[FotoResponse] = []

    for file in files:
        if file.content_type not in settings.ALLOWED_FOTO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Tipo de arquivo não suportado: {file.content_type}. "
                    f"Aceitos: {', '.join(settings.ALLOWED_FOTO_TYPES)}."
                ),
            )

        conteudo = await file.read()
        if len(conteudo) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Cada foto deve ter no máximo {settings.MAX_FOTO_SIZE_MB} MB.",
            )

        extensao = _EXTENSAO_POR_TIPO[file.content_type]
        path = f"{evento.id}/{uuid.uuid4()}.{extensao}"
        await supabase_storage.upload_foto_evento(conteudo, path, file.content_type)

        # Galeria grátis: preco=0; sem thumbnail real (mesmo objeto do original).
        foto = FotoEvento(
            evento_id=evento.id,
            url_thumbnail=path,
            url_original=path,
            preco=0,
        )
        await foto_repo.create(db, foto)
        publicadas.append(_to_response(foto))

    return publicadas


async def listar_por_evento(
    db: AsyncSession, evento_id: uuid.UUID
) -> list[FotoResponse]:
    """Lista as fotos do evento com URLs assinadas (exige login na rota)."""
    evento = await evento_repo.get_by_id(db, evento_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    fotos = await foto_repo.list_by_evento(db, evento_id)
    return [_to_response(foto) for foto in fotos]


async def excluir(
    db: AsyncSession, organizador: Usuario, foto_id: uuid.UUID
) -> None:
    foto = await foto_repo.get_by_id(db, foto_id)
    if foto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada.",
        )
    await _validar_ownership_evento(db, organizador, foto.evento_id)

    # Remoção do storage é best-effort — não bloqueia a exclusão do registro.
    if supabase_storage is not None:
        try:
            supabase_storage.remover_foto(foto.url_original)
        except Exception:
            pass

    await foto_repo.delete(db, foto)


def _to_response(foto: FotoEvento) -> FotoResponse:
    """Monta o response gerando URLs assinadas (bucket privado)."""
    if supabase_storage is None:
        url = ""
    else:
        url = supabase_storage.criar_signed_url(foto.url_original)
    # v1 sem Pillow: thumbnail e original apontam para o mesmo objeto.
    return FotoResponse.from_foto(foto, url_thumbnail=url, url_original=url)


async def _validar_ownership_evento(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
):
    evento = await evento_repo.get_by_id(db, evento_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    if evento.organizador_id != organizador.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é o organizador deste evento.",
        )
    return evento
