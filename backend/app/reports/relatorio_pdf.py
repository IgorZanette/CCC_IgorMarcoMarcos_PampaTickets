import io
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports import branding


@dataclass
class DadosLote:
    nome: str
    tipo: str
    preco_unitario: float
    vendidos: int
    cortesias: int
    checkins: int
    receita: float


@dataclass
class DadosRelatorio:
    evento_nome: str
    evento_data: datetime
    evento_local: str
    lotes: list[DadosLote]
    receita_bruta: float
    desconto_cupons: float
    valor_reembolsado: float
    receita_liquida: float
    total_ingressos: int
    total_checkins: int
    taxa_comparecimento: float  # 0.0–1.0
    gerado_em: datetime


def gerar_pdf_relatorio(dados: DadosRelatorio) -> BinaryIO:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RelTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=4,
        alignment=1,
        textColor=branding.VERDE,
    )
    subtitle_style = ParagraphStyle(
        "RelSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=2,
        alignment=1,
        textColor=branding.GOLD,
    )
    section_style = ParagraphStyle(
        "RelSection",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=6,
        textColor=branding.VERDE,
    )
    normal_style = ParagraphStyle(
        "RelNormal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.HexColor("#2d3748"),
    )
    footer_style = ParagraphStyle(
        "RelFooter",
        parent=styles["Italic"],
        fontSize=8,
        alignment=1,
        textColor=colors.HexColor("#718096"),
    )

    story = []

    # Cabeçalho
    logo = branding.logo_flowable(width_cm=2.6)
    if logo is not None:
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("PampaTickets", title_style))
    story.append(Paragraph("Relatório Financeiro", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"))
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"<b>Evento:</b> {dados.evento_nome}", normal_style))
    story.append(
        Paragraph(
            f"<b>Data do evento:</b> {dados.evento_data.strftime('%d/%m/%Y %H:%M')}",
            normal_style,
        )
    )
    story.append(Paragraph(f"<b>Local:</b> {dados.evento_local}", normal_style))
    story.append(Spacer(1, 0.5 * cm))

    # Resumo executivo
    story.append(Paragraph("Resumo Financeiro", section_style))

    resumo_data = [
        ["Métrica", "Valor"],
        ["Total de ingressos vendidos", str(dados.total_ingressos)],
        ["Total de check-ins realizados", str(dados.total_checkins)],
        [
            "Taxa de comparecimento",
            f"{dados.taxa_comparecimento * 100:.1f}%",
        ],
        ["Receita bruta", f"R$ {dados.receita_bruta:,.2f}"],
        ["Descontos de cupons", f"R$ {dados.desconto_cupons:,.2f}"],
        ["Reembolsos", f"R$ {dados.valor_reembolsado:,.2f}"],
        ["Receita líquida", f"R$ {dados.receita_liquida:,.2f}"],
    ]

    resumo_table = Table(resumo_data, colWidths=[10 * cm, 6 * cm])
    resumo_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), branding.VERDE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f7fafc")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                # Destaque na linha de receita líquida
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), branding.VERDE_SOFT),
            ]
        )
    )
    story.append(resumo_table)

    # Detalhamento por lote
    if dados.lotes:
        story.append(Paragraph("Detalhamento por Lote", section_style))

        lote_header = [
            "Lote",
            "Tipo",
            "Preço Unit.",
            "Vendidos",
            "Cortesias",
            "Check-ins",
            "Receita",
        ]
        lote_rows = [lote_header]
        for lote in dados.lotes:
            lote_rows.append(
                [
                    lote.nome,
                    lote.tipo,
                    f"R$ {lote.preco_unitario:,.2f}",
                    str(lote.vendidos),
                    str(lote.cortesias),
                    str(lote.checkins),
                    f"R$ {lote.receita:,.2f}",
                ]
            )

        col_widths = [4.5 * cm, 2.5 * cm, 2.5 * cm, 1.8 * cm, 2 * cm, 2 * cm, 2.7 * cm]
        lote_table = Table(lote_rows, colWidths=col_widths)
        lote_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), branding.VERDE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 1), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f7fafc")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(lote_table)

    # Rodapé
    story.append(Spacer(1, 1 * cm))
    story.append(
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"))
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"Gerado em {dados.gerado_em.strftime('%d/%m/%Y às %H:%M')} — PampaTickets",
            footer_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer
