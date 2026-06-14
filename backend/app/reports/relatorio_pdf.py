import io
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER
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


def _hex(cor: Color) -> str:
    return f"#{int(cor.red * 255):02x}{int(cor.green * 255):02x}{int(cor.blue * 255):02x}"


def gerar_pdf_relatorio(dados: DadosRelatorio) -> BinaryIO:
    """Relatório financeiro no tema escuro da plataforma — visual de "resumo do
    dashboard", com cards de métrica e tabela escura, em vez de um documento
    genérico claro."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RelTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_LIGHT,
    )
    subtitle_style = ParagraphStyle(
        "RelSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=branding.ACCENT,
    )
    section_style = ParagraphStyle(
        "RelSection",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
        textColor=branding.TEXTO_LIGHT,
    )
    info_style = ParagraphStyle(
        "RelInfo",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=3,
        textColor=branding.TEXTO_DIM_DARK,
    )
    footer_style = ParagraphStyle(
        "RelFooter",
        parent=styles["Italic"],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_DIM_DARK,
    )
    card_label = ParagraphStyle(
        "CardLabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=branding.TEXTO_DIM_DARK,
        leading=10,
    )

    def card_value(cor: Color) -> ParagraphStyle:
        return ParagraphStyle(
            "CardValue",
            parent=styles["Normal"],
            fontSize=17,
            leading=20,
            textColor=cor,
        )

    story: list = []

    # Cabeçalho com logo
    logo = branding.logo_flowable(width_cm=2.6)
    if logo is not None:
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("PampaTickets", title_style))
    story.append(Paragraph("Relatório Financeiro", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=0.7, color=branding.BORDA_DARK))
    story.append(Spacer(1, 0.3 * cm))

    info_label = f'<font color="{_hex(branding.TEXTO_LIGHT)}"><b>{{}}</b></font> {{}}'
    story.append(
        Paragraph(info_label.format("Evento:", dados.evento_nome), info_style)
    )
    story.append(
        Paragraph(
            info_label.format(
                "Data:", dados.evento_data.strftime("%d/%m/%Y %H:%M")
            ),
            info_style,
        )
    )
    story.append(Paragraph(info_label.format("Local:", dados.evento_local), info_style))
    story.append(Spacer(1, 0.4 * cm))

    # Cards de métrica (grid 2 colunas com gaps, estilo dashboard)
    story.append(Paragraph("Resumo financeiro", section_style))

    def card(label: str, valor: str, cor: Color) -> list:
        return [
            Paragraph(label.upper(), card_label),
            Spacer(1, 5),
            Paragraph(f"<b>{valor}</b>", card_value(cor)),
        ]

    metricas = [
        card("Ingressos vendidos", str(dados.total_ingressos), branding.ACCENT),
        card("Check-ins realizados", str(dados.total_checkins), branding.TEXTO_LIGHT),
        card("Taxa de comparecimento", f"{dados.taxa_comparecimento * 100:.1f}%", branding.GOLD_CLARO),
        card("Receita bruta", f"R$ {dados.receita_bruta:,.2f}", branding.TEXTO_LIGHT),
        card("Descontos de cupons", f"R$ {dados.desconto_cupons:,.2f}", branding.TEXTO_LIGHT),
        card("Reembolsos", f"R$ {dados.valor_reembolsado:,.2f}", branding.TEXTO_LIGHT),
    ]

    largura_card = 7.7 * cm
    gap = 0.4 * cm
    grid_rows: list = []
    estilo_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]
    linha = 0
    for i in range(0, len(metricas), 2):
        esquerda = metricas[i]
        direita = metricas[i + 1] if i + 1 < len(metricas) else ""
        grid_rows.append([esquerda, "", direita])
        # Cards = fundo do card; preenchimento interno simulado com padding.
        for col in (0, 2):
            estilo_cmds += [
                ("BACKGROUND", (col, linha), (col, linha), branding.BG_CARD),
                ("LEFTPADDING", (col, linha), (col, linha), 14),
                ("RIGHTPADDING", (col, linha), (col, linha), 14),
                ("TOPPADDING", (col, linha), (col, linha), 12),
                ("BOTTOMPADDING", (col, linha), (col, linha), 12),
                ("LINEBELOW", (col, linha), (col, linha), 2, branding.BG),
                ("LINEABOVE", (col, linha), (col, linha), 2, branding.BG),
            ]
        linha += 1

    grid = Table(grid_rows, colWidths=[largura_card, gap, largura_card])
    grid.setStyle(TableStyle(estilo_cmds))
    story.append(grid)
    story.append(Spacer(1, 0.35 * cm))

    # Card de destaque: receita líquida (largura total)
    destaque = Table(
        [
            [
                Paragraph("RECEITA LÍQUIDA", card_label),
                Paragraph(
                    f'<font size="22" color="{_hex(branding.ACCENT)}"><b>'
                    f"R$ {dados.receita_liquida:,.2f}</b></font>",
                    ParagraphStyle("Liq", parent=styles["Normal"], alignment=2),
                ),
            ]
        ],
        colWidths=[8 * cm, 7.8 * cm],
    )
    destaque.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), branding.ACCENT_SOFT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LINEBELOW", (0, 0), (-1, -1), 1, branding.ACCENT),
            ]
        )
    )
    story.append(destaque)

    # Detalhamento por lote — tabela escura
    if dados.lotes:
        story.append(Paragraph("Detalhamento por lote", section_style))

        header = ["Lote", "Tipo", "Preço Unit.", "Vendidos", "Cortesias", "Check-ins", "Receita"]
        linhas = [header]
        for lote in dados.lotes:
            linhas.append(
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

        col_widths = [4.3 * cm, 2.3 * cm, 2.4 * cm, 1.8 * cm, 2 * cm, 2 * cm, 2.6 * cm]
        tabela = Table(linhas, colWidths=col_widths)
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), branding.VERDE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), branding.TEXTO_LIGHT),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 1), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 1), (-1, -1), branding.TEXTO_LIGHT),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [branding.BG_CARD, branding.BG_CARD_2],
                    ),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, branding.BORDA_DARK),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(tabela)

    # Rodapé
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=branding.BORDA_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"Gerado em {dados.gerado_em.strftime('%d/%m/%Y às %H:%M')} — PampaTickets",
            footer_style,
        )
    )

    doc.build(
        story,
        onFirstPage=branding.pintar_fundo_dark,
        onLaterPages=branding.pintar_fundo_dark,
    )
    buffer.seek(0)
    return buffer
