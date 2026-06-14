import io
from datetime import datetime, timezone
from typing import BinaryIO

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
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

from app.models.ingresso import Ingresso
from app.reports import branding


def gerar_pdf_ingresso(ingresso: Ingresso) -> BinaryIO:
    """PDF do ingresso no tema escuro da plataforma, com QR Code real em
    destaque e visual alinhado ao app."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
    )

    styles = getSampleStyleSheet()
    eyebrow = ParagraphStyle(
        "Eyebrow",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=branding.GOLD_CLARO,
        spaceAfter=2,
    )
    marca = ParagraphStyle(
        "Marca",
        parent=styles["Heading1"],
        fontSize=22,
        alignment=TA_CENTER,
        textColor=branding.ACCENT,
        spaceAfter=2,
    )
    evento_nome_style = ParagraphStyle(
        "EventoNome",
        parent=styles["Heading2"],
        fontSize=18,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_LIGHT,
        spaceAfter=4,
    )
    evento_meta_style = ParagraphStyle(
        "EventoMeta",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_LIGHT,
        leading=16,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        textColor=branding.TEXTO_DIM_DARK,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=11,
        textColor=branding.TEXTO_LIGHT,
        leading=14,
    )
    qr_hint = ParagraphStyle(
        "QrHint",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_DIM_DARK,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Italic"],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=branding.TEXTO_DIM_DARK,
    )

    evento = ingresso.lote.evento
    usuario = ingresso.participante

    story: list = []

    logo = branding.logo_flowable(width_cm=3.2)
    if logo is not None:
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("PampaTickets", marca))
    story.append(Paragraph("INGRESSO", eyebrow))
    story.append(Spacer(1, 0.4 * cm))

    # Faixa de destaque do evento (verde, texto branco)
    data_fmt = evento.data_inicio.strftime("%d/%m/%Y às %H:%M")
    destaque = Table(
        [
            [Paragraph(evento.nome, evento_nome_style)],
            [Paragraph(f"{data_fmt}<br/>{evento.local}", evento_meta_style)],
        ],
        colWidths=[16 * cm],
    )
    destaque.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), branding.VERDE),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ]
        )
    )
    story.append(destaque)
    story.append(Spacer(1, 0.6 * cm))

    # QR Code real, centralizado (fundo branco — mantém escaneável no escuro)
    qr = branding.qrcode_flowable(ingresso.qr_code_hash, size_cm=4.8)
    qr.hAlign = "CENTER"
    story.append(qr)
    story.append(Paragraph("Apresente este QR Code na entrada", qr_hint))
    story.append(Spacer(1, 0.6 * cm))

    def campo(label: str, valor: str):
        return [Paragraph(label.upper(), label_style), Paragraph(valor, value_style)]

    status_cor = (
        branding.ACCENT if ingresso.status.value == "ATIVO" else branding.BORDEAUX
    )
    status_style = ParagraphStyle(
        "Status", parent=value_style, textColor=status_cor, fontSize=11
    )

    detalhes = Table(
        [
            campo("Participante", usuario.nome)
            + campo("Categoria / Lote", ingresso.lote.nome),
            campo("CPF/CNPJ", usuario.cpf_cnpj)
            + campo("Valor", f"R$ {ingresso.lote.preco:.2f}"),
            campo("E-mail", usuario.email)
            + [
                Paragraph("STATUS", label_style),
                Paragraph(ingresso.status.value, status_style),
            ],
        ],
        colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm],
    )
    detalhes.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, branding.BORDA_DARK),
            ]
        )
    )
    story.append(detalhes)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("CÓDIGO DO INGRESSO", label_style))
    story.append(
        Paragraph(
            f"<font face='Courier'>{ingresso.id}</font>",
            ParagraphStyle("Codigo", parent=value_style, fontSize=9),
        )
    )

    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=branding.BORDA_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "PampaTickets — Sistema de Gestão de Eventos · "
            f"Emitido em {ingresso.emitido_em.strftime('%d/%m/%Y %H:%M')}",
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


def gerar_pdf_certificado(ingresso: Ingresso) -> BinaryIO:
    """Certificado de participação em paisagem, tema claro, com borda dupla decorativa."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=3.2 * cm,
        leftMargin=3.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    marca_style = ParagraphStyle(
        "CertMarca",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=branding.CERT_TEXTO_DIM,
        spaceAfter=0,
        leading=14,
    )
    titulo = ParagraphStyle(
        "CertTitulo",
        parent=styles["Heading1"],
        fontSize=36,
        alignment=TA_CENTER,
        textColor=branding.CERT_BORDA_EXT,
        spaceAfter=2,
        leading=42,
    )
    subtitulo = ParagraphStyle(
        "CertSubtitulo",
        parent=styles["Normal"],
        fontSize=13,
        alignment=TA_CENTER,
        textColor=branding.CERT_BORDA_INT,
        spaceAfter=0,
        leading=18,
        charSpace=3,
    )
    intro = ParagraphStyle(
        "CertIntro",
        parent=styles["Normal"],
        fontSize=13,
        alignment=TA_CENTER,
        textColor=branding.CERT_TEXTO_DIM,
        spaceAfter=4,
        leading=18,
    )
    nome_style = ParagraphStyle(
        "CertNome",
        parent=styles["Heading2"],
        fontSize=30,
        alignment=TA_CENTER,
        textColor=branding.CERT_BORDA_EXT,
        spaceAfter=6,
        leading=36,
    )
    corpo = ParagraphStyle(
        "CertCorpo",
        parent=styles["Normal"],
        fontSize=13,
        alignment=TA_CENTER,
        textColor=branding.CERT_TEXTO,
        spaceAfter=0,
        leading=20,
    )
    rodape_style = ParagraphStyle(
        "CertRodape",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=branding.CERT_TEXTO_DIM,
        leading=13,
    )

    evento = ingresso.lote.evento
    usuario = ingresso.participante
    data_evento = evento.data_inicio.strftime("%d/%m/%Y")
    data_emissao = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    story: list = []

    logo = branding.logo_flowable(width_cm=1.8)
    if logo is not None:
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("PampaTickets", marca_style))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        HRFlowable(width="35%", thickness=1, color=branding.CERT_BORDA_INT, hAlign="CENTER")
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("CERTIFICADO", titulo))
    story.append(Paragraph("DE PARTICIPAÇÃO", subtitulo))

    story.append(Spacer(1, 0.7 * cm))

    story.append(Paragraph("Certificamos que", intro))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(usuario.nome, nome_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"participou do evento <b>{evento.nome}</b>, "
            f"realizado em {data_evento}, no local {evento.local}.",
            corpo,
        )
    )

    story.append(Spacer(1, 0.9 * cm))
    story.append(
        HRFlowable(width="45%", thickness=1, color=branding.CERT_BORDA_EXT, hAlign="CENTER")
    )
    story.append(Spacer(1, 0.3 * cm))

    story.append(
        Paragraph(
            f"PampaTickets — Sistema de Gestão de Eventos<br/>"
            f"Emitido em {data_emissao}",
            rodape_style,
        )
    )

    doc.build(
        story,
        onFirstPage=branding.pintar_fundo_certificado,
        onLaterPages=branding.pintar_fundo_certificado,
    )
    buffer.seek(0)
    return buffer
