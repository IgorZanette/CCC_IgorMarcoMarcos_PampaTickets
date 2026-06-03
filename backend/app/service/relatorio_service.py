import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cortesia import Cortesia
from app.models.ingresso import Ingresso, StatusIngresso
from app.models.lote import Lote
from app.models.pagamento import Pagamento, Reembolso
from app.models.pedido import Pedido, PedidoItem, StatusPedido
from app.models.usuario import Usuario
from app.reports.relatorio_pdf import DadosLote, DadosRelatorio, gerar_pdf_relatorio
from app.repositories import evento_repo

# Receita só de pedidos efetivamente pagos (não-reembolsados). Pedidos REEMBOLSADO
# saem da receita; o total reembolsado é reportado à parte (#16).
_STATUS_FATURADOS = (StatusPedido.PAGO,)


async def gerar_relatorio(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
):
    dados = await montar_dados(db, organizador, evento_id)
    return gerar_pdf_relatorio(dados)


async def montar_dados(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
) -> DadosRelatorio:
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

    # Q1 — vendas/receita por lote (somente pedidos PAGO). O filtro de status entra
    # via CASE no agregado, não no JOIN: caso contrário, itens de pedidos não-pagos
    # (pendentes, cancelados, reembolsados) vazariam no somatório de receita.
    faturado = Pedido.status.in_(_STATUS_FATURADOS)
    vendas_stmt = (
        select(
            Lote.id,
            Lote.nome,
            Lote.tipo,
            Lote.preco,
            func.coalesce(
                func.sum(case((faturado, PedidoItem.quantidade), else_=0)), 0
            ).label("vendidos"),
            func.coalesce(
                func.sum(
                    case(
                        (faturado, PedidoItem.quantidade * PedidoItem.preco_unitario),
                        else_=0,
                    )
                ),
                0,
            ).label("receita"),
        )
        .join(PedidoItem, PedidoItem.lote_id == Lote.id, isouter=True)
        .join(Pedido, Pedido.id == PedidoItem.pedido_id, isouter=True)
        .where(Lote.evento_id == evento_id)
        .group_by(Lote.id, Lote.nome, Lote.tipo, Lote.preco)
    )
    vendas_result = await db.execute(vendas_stmt)
    vendas_por_lote = {row.id: row for row in vendas_result.all()}

    # Q2 — total de descontos de cupons
    desconto_stmt = select(func.coalesce(func.sum(Pedido.valor_desconto), 0)).where(
        Pedido.evento_id == evento_id,
        Pedido.status.in_(_STATUS_FATURADOS),
    )
    desconto_total = float((await db.execute(desconto_stmt)).scalar_one())

    # Q3 — reembolsos (join Reembolso → Pagamento → Pedido)
    reembolso_stmt = (
        select(func.coalesce(func.sum(Reembolso.valor_reembolsado), 0))
        .join(Pagamento, Pagamento.id == Reembolso.pagamento_id)
        .join(Pedido, Pedido.id == Pagamento.pedido_id)
        .where(
            Pedido.evento_id == evento_id,
            Reembolso.processado_em.isnot(None),
        )
    )
    valor_reembolsado = float((await db.execute(reembolso_stmt)).scalar_one())

    # Q4 — cortesias por lote
    cortesia_stmt = (
        select(Cortesia.lote_id, func.count(Cortesia.id).label("total"))
        .where(Cortesia.evento_id == evento_id)
        .group_by(Cortesia.lote_id)
    )
    cortesias_por_lote: dict[uuid.UUID, int] = {
        row.lote_id: row.total for row in (await db.execute(cortesia_stmt)).all()
    }

    # Q5 — check-ins por lote (Ingresso UTILIZADO cujo lote pertence ao evento)
    checkin_stmt = (
        select(Ingresso.lote_id, func.count(Ingresso.id).label("total"))
        .join(Lote, Lote.id == Ingresso.lote_id)
        .where(Lote.evento_id == evento_id, Ingresso.status == StatusIngresso.UTILIZADO)
        .group_by(Ingresso.lote_id)
    )
    checkins_por_lote: dict[uuid.UUID, int] = {
        row.lote_id: row.total for row in (await db.execute(checkin_stmt)).all()
    }

    # Montar lista de lotes
    lotes: list[DadosLote] = []
    for lote_id, row in vendas_por_lote.items():
        lotes.append(
            DadosLote(
                nome=row.nome,
                tipo=row.tipo.value if hasattr(row.tipo, "value") else str(row.tipo),
                preco_unitario=float(row.preco),
                vendidos=int(row.vendidos),
                cortesias=cortesias_por_lote.get(lote_id, 0),
                checkins=checkins_por_lote.get(lote_id, 0),
                receita=float(row.receita),
            )
        )

    receita_bruta = sum(lote.receita for lote in lotes)
    # Pedidos reembolsados já não entram na receita_bruta; o reembolso é informativo.
    receita_liquida = receita_bruta - desconto_total
    total_ingressos = sum(lote.vendidos + lote.cortesias for lote in lotes)
    total_checkins = sum(lote.checkins for lote in lotes)
    taxa_comparecimento = (
        total_checkins / total_ingressos if total_ingressos > 0 else 0.0
    )

    dados = DadosRelatorio(
        evento_nome=evento.nome,
        evento_data=evento.data_inicio,
        evento_local=evento.local,
        lotes=lotes,
        receita_bruta=receita_bruta,
        desconto_cupons=desconto_total,
        valor_reembolsado=valor_reembolsado,
        receita_liquida=receita_liquida,
        total_ingressos=total_ingressos,
        total_checkins=total_checkins,
        taxa_comparecimento=taxa_comparecimento,
        gerado_em=datetime.now(timezone.utc),
    )

    return dados
