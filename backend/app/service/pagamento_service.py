from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.asaas import charges as asaas_charges
from app.models.pagamento import MetodoPagamento, StatusPagamento
from app.models.pedido import Pedido, StatusPedido
from app.repositories import pagamento_repo
from app.service.ingresso_service import gerar_pdf_ingresso_upload
from app.repositories import ingresso_repo


async def criar_pagamento(
    db: AsyncSession,
    *,
    pedido: Pedido,
    metodo: MetodoPagamento,
    customer_id: str,
) -> dict:
    """
    Cria o registro de pagamento no banco e a cobrança no Asaas.
    Retorna o dict da cobrança do Asaas (contém o link/QR Code).
    """
    pagamento = await pagamento_repo.create(
        db,
        pedido_id=pedido.id,
        metodo=metodo,
        valor=float(pedido.valor_total),
    )

    cobranca = await asaas_charges.create_charge(
        customer_id=customer_id,
        billing_type=metodo.value,
        value=float(pedido.valor_total),
        due_date=datetime.now(timezone.utc).date(),
        external_reference=str(pedido.id),
    )

    await pagamento_repo.update_charge_id(db, pagamento, cobranca["id"])

    return cobranca


async def obter_pix_qrcode(charge_id: str) -> dict:
    return await asaas_charges.get_pix_qrcode(charge_id=charge_id)


async def processar_webhook(db: AsyncSession, *, evento: str, payment_id: str) -> None:
    """
    Processa eventos recebidos do Asaas e atualiza o banco.
    Deve ser chamado pelo webhook_service após validar o token.
    """
    pagamento = await pagamento_repo.get_by_charge_id(db, payment_id)
    if pagamento is None:
        return

    if evento in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
        await pagamento_repo.update_status(
            db,
            pagamento,
            StatusPagamento.APROVADO,
            pago_em=datetime.now(timezone.utc),
        )
        await _atualizar_status_pedido(db, pagamento.pedido_id, StatusPedido.PAGO)

        # Gerar PDFs dos ingressos automaticamente
        await _gerar_pdfs_ingressos(db, pagamento.pedido_id)

    elif evento == "PAYMENT_OVERDUE":
        await pagamento_repo.update_status(db, pagamento, StatusPagamento.RECUSADO)
        await _atualizar_status_pedido(db, pagamento.pedido_id, StatusPedido.CANCELADO)

    elif evento == "PAYMENT_REFUNDED":
        await pagamento_repo.update_status(db, pagamento, StatusPagamento.ESTORNADO)
        await _atualizar_status_pedido(
            db, pagamento.pedido_id, StatusPedido.REEMBOLSADO
        )


async def _atualizar_status_pedido(
    db: AsyncSession, pedido_id, novo_status: StatusPedido
) -> None:
    result = await db.get(Pedido, pedido_id)
    if result is not None:
        result.status = novo_status
        await db.commit()


async def _gerar_pdfs_ingressos(db: AsyncSession, pedido_id: str) -> None:
    """
    Gera PDFs para todos os ingressos de um pedido pago.
    """
    try:
        # Buscar ingressos do pedido
        ingressos = await ingresso_repo.get_by_pedido_id(db, pedido_id)

        # Gerar PDF para cada ingresso
        for ingresso in ingressos:
            await gerar_pdf_ingresso_upload(db, str(ingresso.id))

    except Exception as e:
        # Log do erro, mas não falha o webhook
        pass
