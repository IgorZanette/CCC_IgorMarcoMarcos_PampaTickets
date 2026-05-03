from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.supabase_storage import supabase_storage
from app.models.ingresso import Ingresso, StatusIngresso
from app.reports.ingresso_pdf import gerar_pdf_certificado, gerar_pdf_ingresso
from app.repositories import ingresso_repo


async def gerar_pdf_ingresso_upload(
    db: AsyncSession,
    ingresso_id: str
) -> Optional[str]:
    """
    Gera PDF do ingresso e faz upload para Supabase Storage.

    Args:
        db: Sessão do banco de dados
        ingresso_id: ID do ingresso

    Returns:
        URL do PDF no Supabase, ou None se erro ou não configurado
    """
    try:
        # Verificar se Supabase está configurado
        from app.core.config import settings
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or supabase_storage is None:
            return None

        # Buscar ingresso com relacionamentos
        ingresso = await ingresso_repo.get_with_relations(db, ingresso_id)
        if not ingresso:
            return None

        # Gerar PDF
        pdf_buffer = gerar_pdf_ingresso(ingresso)

        # Nome do arquivo
        filename = f"ingresso_{ingresso_id}.pdf"

        # Upload para Supabase
        pdf_url = await supabase_storage.upload_ingresso_pdf(
            file=pdf_buffer,
            filename=filename,
            ingresso_id=ingresso_id
        )

        # Atualizar URL no banco
        await ingresso_repo.update_pdf_url(db, ingresso_id, pdf_url)

        return pdf_url

    except Exception as e:
        # Log do erro (já feito pelo middleware)
        return None


async def gerar_pdf_certificado_upload(
    db: AsyncSession,
    ingresso_id: str
) -> Optional[str]:
    """
    Gera PDF do certificado e faz upload para Supabase Storage.

    Args:
        db: Sessão do banco de dados
        ingresso_id: ID do ingresso (deve estar UTILIZADO)

    Returns:
        URL do PDF no Supabase, ou None se erro ou não configurado
    """
    try:
        # Verificar se Supabase está configurado
        from app.core.config import settings
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or supabase_storage is None:
            return None

        # Buscar ingresso com relacionamentos
        ingresso = await ingresso_repo.get_with_relations(db, ingresso_id)
        if not ingresso or ingresso.status != StatusIngresso.UTILIZADO:
            return None

        # Gerar PDF do certificado
        pdf_buffer = gerar_pdf_certificado(ingresso)

        # Nome do arquivo
        filename = f"certificado_{ingresso_id}.pdf"

        # Upload para Supabase
        pdf_url = await supabase_storage.upload_certificado_pdf(
            file=pdf_buffer,
            filename=filename,
            ingresso_id=ingresso_id
        )

        # Atualizar URL no banco (campo certificado_url se existir)
        # Por enquanto, apenas retornamos a URL
        # await ingresso_repo.update_certificado_url(db, ingresso_id, pdf_url)

        return pdf_url

    except Exception as e:
        # Log do erro (já feito pelo middleware)
        return None


async def validar_checkin(
    db: AsyncSession,
    qr_code_hash: str
) -> Optional[dict]:
    """
    Valida um ingresso via QR Code hash e marca como utilizado.

    Args:
        db: Sessão do banco de dados
        qr_code_hash: Hash do QR Code do ingresso

    Returns:
        Dados do ingresso se válido, None se inválido
    """
    try:
        ingresso = await ingresso_repo.get_by_qr_hash(db, qr_code_hash)
        if not ingresso or ingresso.status != StatusIngresso.ATIVO:
            return None

        # Marcar como utilizado
        await ingresso_repo.update_status(db, ingresso.id, StatusIngresso.UTILIZADO)

        # Gerar certificado automaticamente
        certificado_url = await gerar_pdf_certificado_upload(db, str(ingresso.id))

        return {
            "ingresso_id": ingresso.id,
            "evento_nome": ingresso.pedido.lote.evento.nome,
            "participante_nome": ingresso.pedido.usuario.nome,
            "certificado_url": certificado_url
        }

    except Exception as e:
        # Log do erro
        return None