import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import aware_utc
from app.integrations.asaas import charges as asaas_charges
from app.integrations.asaas.exceptions import AsaasAPIError
from app.models.evento import StatusEvento
from app.models.ingresso import StatusIngresso
from app.models.pagamento import MetodoPagamento, Reembolso, StatusPagamento
from app.models.pedido import Pedido, PedidoItem, StatusPedido
from app.models.usuario import Usuario
from app.repositories import (
    cupom_repo,
    evento_repo,
    ingresso_repo,
    lote_repo,
    pagamento_repo,
    pedido_repo,
    reembolso_repo,
)
from app.schemas.pedido import PedidoCreate
from app.service import cancelamento_service, cupom_service, pagamento_service


async def criar(db: AsyncSession, participante: Usuario, data: PedidoCreate) -> dict:
    evento = await evento_repo.get_by_id(db, data.evento_id)
    if evento is None or evento.status != StatusEvento.PUBLICADO:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado ou não está publicado.",
        )

    if not participante.asaas_customer_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Participante sem cadastro no gateway de pagamento.",
        )

    agora = datetime.now(timezone.utc)
    lotes_validos: list[tuple] = []
    valor_total = Decimal("0")

    for item in data.itens:
        lote = await lote_repo.get_by_id_for_update(db, item.lote_id)

        if lote is None or lote.evento_id != evento.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {item.lote_id} não encontrado neste evento.",
            )
        if not lote.ativo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lote '{lote.nome}' não está disponível para venda.",
            )
        inicio_venda = aware_utc(lote.data_inicio_venda)
        fim_venda = aware_utc(lote.data_fim_venda)
        if not (inicio_venda <= agora <= fim_venda):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lote '{lote.nome}' está fora da janela de venda.",
            )
        disponivel = lote.quantidade_total - lote.quantidade_vendida
        if item.quantidade > disponivel:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Lote '{lote.nome}' possui apenas {disponivel} "
                    "ingresso(s) disponível(is)."
                ),
            )

        valor_total += lote.preco * item.quantidade
        lotes_validos.append((lote, item.quantidade))

    cupom = None
    valor_desconto = Decimal("0")
    if data.cupom_codigo:
        cupom, valor_desconto = await cupom_service.validar_e_calcular_desconto(
            db,
            evento_id=evento.id,
            codigo=data.cupom_codigo,
            valor_base=valor_total,
            for_update=True,
        )

    valor_total = (valor_total - valor_desconto).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    pedido = Pedido(
        participante_id=participante.id,
        evento_id=evento.id,
        cupom_id=cupom.id if cupom is not None else None,
        valor_total=valor_total,
        valor_desconto=valor_desconto,
    )
    db.add(pedido)
    await db.flush()

    for lote, qtd in lotes_validos:
        db.add(
            PedidoItem(
                pedido_id=pedido.id,
                lote_id=lote.id,
                quantidade=qtd,
                preco_unitario=lote.preco,
            )
        )
        lote_repo.incrementar_vendidas(lote, qtd)

    if cupom is not None:
        cupom_repo.incrementar_usado(cupom)

    await db.commit()
    await db.refresh(pedido)

    try:
        cobranca = await pagamento_service.criar_pagamento(
            db,
            pedido=pedido,
            metodo=data.metodo,
            customer_id=participante.asaas_customer_id,
        )
    except AsaasAPIError as exc:
        for lote, qtd in lotes_validos:
            lote_repo.decrementar_vendidas(lote, qtd)
        if cupom is not None:
            cupom_repo.decrementar_usado(cupom)
        pedido.status = StatusPedido.CANCELADO
        await db.commit()
        if exc.is_client_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.user_message,
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gateway de pagamento indisponível. Tente novamente em instantes.",
        )

    pedido_com_itens = await pedido_repo.get_by_id_com_itens(db, pedido.id)

    pix_qrcode = None
    if data.metodo == MetodoPagamento.PIX:
        charge_id = cobranca.get("id", "")
        if charge_id:
            try:
                pix_qrcode = await asaas_charges.get_pix_qrcode(charge_id=charge_id)
            except AsaasAPIError:
                logger.warning("Falha ao buscar QR Code PIX para charge {}", charge_id)
                pass

    return {
        "pedido": pedido_com_itens,
        "invoice_url": cobranca.get("invoiceUrl", ""),
        "charge_id": cobranca.get("id", ""),
        "pix_qrcode": pix_qrcode,
    }


async def obter(db: AsyncSession, usuario: Usuario, pedido_id: uuid.UUID) -> Pedido:
    pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )
    if pedido.participante_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este pedido.",
        )
    return pedido


async def listar_meus(db: AsyncSession, participante: Usuario) -> list[Pedido]:
    return await pedido_repo.list_by_participante(db, participante.id)


async def cancelar(
    db: AsyncSession, participante: Usuario, pedido_id: uuid.UUID
) -> Pedido:
    pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )
    if pedido.participante_id != participante.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este pedido.",
        )
    if pedido.status != StatusPedido.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas pedidos pendentes podem ser cancelados.",
        )

    return await cancelamento_service.aplicar_cancelamento(
        db,
        pedido=pedido,
        motivo_status_pagamento=StatusPagamento.CANCELADO,
    )


async def reembolsar(
    db: AsyncSession,
    participante: Usuario,
    pedido_id: uuid.UUID,
    motivo: str | None,
) -> Reembolso:
    pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )
    if pedido.participante_id != participante.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este pedido.",
        )
    if pedido.status != StatusPedido.PAGO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas pedidos pagos podem ser reembolsados.",
        )

    ingressos = await ingresso_repo.get_by_pedido_id(db, pedido.id)
    if any(i.status == StatusIngresso.UTILIZADO for i in ingressos):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível reembolsar pedido com ingresso já utilizado.",
        )

    pagamento = await pagamento_repo.get_by_pedido_id_for_update(db, pedido.id)
    if pagamento is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pedido sem pagamento associado.",
        )

    existente = await reembolso_repo.get_by_pagamento_id(db, pagamento.id)
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reembolso já solicitado para este pedido.",
        )

    return await pagamento_service.solicitar_reembolso(
        db, pagamento=pagamento, motivo=motivo
    )


async def obter_status_pagamento(
    db: AsyncSession, usuario: Usuario, pedido_id: uuid.UUID
) -> dict:
    """Dados de pagamento do pedido para a tela de status (reidrata PIX/fatura).

    Reconsulta o Asaas para obter a fatura e o QR Code PIX atuais, permitindo que
    a tela funcione mesmo após refresh (quando o state da navegação se perde).
    """
    pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )
    if pedido.participante_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este pedido.",
        )

    pagamento = await pagamento_repo.get_by_pedido_id(db, pedido_id)
    if pagamento is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pedido sem pagamento associado.",
        )

    invoice_url = None
    pix_qrcode = None
    if pagamento.charge_id:
        try:
            cobranca = await asaas_charges.get_charge(charge_id=pagamento.charge_id)
            invoice_url = cobranca.get("invoiceUrl")
        except AsaasAPIError:
            logger.warning(
                "Falha ao consultar cobrança {} para status de pagamento",
                pagamento.charge_id,
            )
        if pagamento.metodo == MetodoPagamento.PIX:
            try:
                pix_qrcode = await asaas_charges.get_pix_qrcode(
                    charge_id=pagamento.charge_id
                )
            except AsaasAPIError:
                logger.warning(
                    "Falha ao buscar QR Code PIX da cobrança {}",
                    pagamento.charge_id,
                )

    return {
        "pedido_id": pedido.id,
        "metodo": pagamento.metodo,
        "status_pagamento": pagamento.status,
        "status_pedido": pedido.status,
        "charge_id": pagamento.charge_id,
        "invoice_url": invoice_url,
        "pix_qrcode": pix_qrcode,
    }
