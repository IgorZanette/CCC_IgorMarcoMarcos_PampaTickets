import secrets
import uuid
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations import email_service
from app.integrations.supabase.supabase_storage import supabase_storage
from app.models.evento import StatusEvento
from app.models.ingresso import Ingresso, StatusIngresso
from app.models.usuario import Usuario
from app.reports import branding
from app.reports.ingresso_pdf import gerar_pdf_certificado, gerar_pdf_ingresso
from app.repositories import certificado_repo, checkin_repo, ingresso_repo, pedido_repo
from app.service import whatsapp_service


async def gerar_pdf_ingresso_upload(
    db: AsyncSession, ingresso_id: str
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

        if (
            not settings.SUPABASE_URL
            or not settings.SUPABASE_KEY
            or supabase_storage is None
        ):
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
            file=pdf_buffer, filename=filename, ingresso_id=ingresso_id
        )

        # Atualizar URL no banco
        await ingresso_repo.update_pdf_url(db, ingresso_id, pdf_url)

        return pdf_url

    except Exception:
        logger.exception("Falha ao gerar/upload do PDF (ingresso_id={})", ingresso_id)
        return None


async def gerar_pdf_certificado_upload(
    db: AsyncSession, ingresso_id: str
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

        if (
            not settings.SUPABASE_URL
            or not settings.SUPABASE_KEY
            or supabase_storage is None
        ):
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
            file=pdf_buffer, filename=filename, ingresso_id=ingresso_id
        )

        # Persistir Certificado no banco (idempotente)
        existente = await certificado_repo.get_by_ingresso_id(db, ingresso.id)
        if existente is None:
            await certificado_repo.create(
                db,
                ingresso_id=ingresso.id,
                participante_id=ingresso.participante_id,
                pdf_url=pdf_url,
            )

        return pdf_url

    except Exception:
        logger.exception("Falha ao gerar/upload do PDF (ingresso_id={})", ingresso_id)
        return None


async def validar_checkin(
    db: AsyncSession,
    *,
    qr_code_hash: str,
    usuario: Usuario,
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    """
    Valida um ingresso via QR Code hash, persiste o Checkin e marca como utilizado.
    Apenas o organizador dono do evento pode operar o check-in.
    """
    ingresso = await ingresso_repo.get_by_qr_hash(db, qr_code_hash)
    if ingresso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingresso não encontrado.",
        )
    if ingresso.lote.evento.organizador_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é o organizador deste evento.",
        )
    if ingresso.lote.evento.status == StatusEvento.CANCELADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evento cancelado — check-in indisponível.",
        )
    if ingresso.status == StatusIngresso.UTILIZADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ingresso já utilizado.",
        )
    if ingresso.status == StatusIngresso.CANCELADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ingresso cancelado.",
        )

    checkin = await checkin_repo.create(
        db, ingresso_id=ingresso.id, realizado_por=usuario.id
    )
    await ingresso_repo.update_status(db, ingresso.id, StatusIngresso.UTILIZADO)

    certificado_url = await gerar_pdf_certificado_upload(db, str(ingresso.id))

    # UC15: notifica o participante (best-effort, em background).
    whatsapp_service.notificar_checkin(
        background_tasks,
        nome=ingresso.participante.nome,
        telefone=ingresso.participante.celular,
        evento_nome=ingresso.lote.evento.nome,
    )

    return {
        "checkin_id": checkin.id,
        "ingresso_id": ingresso.id,
        "realizado_em": checkin.realizado_em,
        "evento_nome": ingresso.lote.evento.nome,
        "participante_nome": ingresso.participante.nome,
        "certificado_url": certificado_url,
    }


async def montar_email_ingresso(db: AsyncSession, ingresso_id: str) -> Optional[dict]:
    """Carrega o ingresso e gera, em memória, os anexos do email (PDF + QR PNG).

    Retorna os argumentos prontos para `email_service.enviar_ingresso_por_email`,
    ou None se o ingresso não existir. Separado do envio para que o SMTP possa
    rodar em background (BackgroundTasks) sem depender da sessão do banco.
    """
    ingresso = await ingresso_repo.get_with_relations(db, ingresso_id)
    if ingresso is None:
        return None

    pdf_bytes = gerar_pdf_ingresso(ingresso).getvalue()
    qr_png_bytes = branding.gerar_qrcode_image(ingresso.qr_code_hash).getvalue()

    evento = ingresso.lote.evento
    return {
        "email_destino": ingresso.participante.email,
        "nome_usuario": ingresso.participante.nome,
        "nome_evento": evento.nome,
        "data_evento_str": evento.data_inicio.strftime("%d/%m/%Y %H:%M"),
        "pdf_bytes": pdf_bytes,
        "qr_png_bytes": qr_png_bytes,
        "nome_pdf": f"ingresso_{ingresso_id}.pdf",
    }


async def enviar_email_ingresso(db: AsyncSession, ingresso_id: str) -> bool:
    """Gera PDF + QR do ingresso em memória e envia por email ao participante."""
    try:
        payload = await montar_email_ingresso(db, ingresso_id)
        if payload is None:
            return False
        return await email_service.enviar_ingresso_por_email(**payload)
    except Exception:
        logger.exception("Falha ao enviar ingresso por email (ingresso_id={})", ingresso_id)
        return False


async def criar_ingressos_para_pedido(
    db: AsyncSession, pedido_id: uuid.UUID
) -> list[Ingresso]:
    """
    Cria 1 Ingresso por unidade em cada PedidoItem do pedido.
    Idempotente: se já existem ingressos para o pedido, retorna os existentes.
    """
    pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
    if pedido is None:
        return []

    existentes = await ingresso_repo.get_by_pedido_id(db, pedido_id)
    if existentes:
        return existentes

    ingressos: list[Ingresso] = []
    for item in pedido.itens:
        for _ in range(item.quantidade):
            ing = Ingresso(
                pedido_item_id=item.id,
                lote_id=item.lote_id,
                participante_id=pedido.participante_id,
                qr_code_hash=secrets.token_urlsafe(32),
                status=StatusIngresso.ATIVO,
            )
            db.add(ing)
            ingressos.append(ing)

    await db.commit()
    for ing in ingressos:
        await db.refresh(ing)
    return ingressos
