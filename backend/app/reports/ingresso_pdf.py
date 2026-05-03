import io
from typing import BinaryIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.ingresso import Ingresso


def gerar_pdf_ingresso(ingresso: Ingresso) -> BinaryIO:
    """
    Gera um PDF para um ingresso individual.

    Args:
        ingresso: Instância do modelo Ingresso com dados relacionados carregados

    Returns:
        Arquivo binário contendo o PDF do ingresso
    """
    buffer = io.BytesIO()

    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Centralizado
        textColor=colors.darkblue
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.darkgreen
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.spaceAfter = 10

    # Conteúdo do PDF
    story = []

    # Título
    story.append(Paragraph("PampaTickets", title_style))
    story.append(Paragraph("Ingresso para Evento", subtitle_style))
    story.append(Spacer(1, 0.5*cm))

    # Dados do evento
    evento = ingresso.pedido.lote.evento
    story.append(Paragraph(f"<b>Evento:</b> {evento.nome}", normal_style))
    story.append(Paragraph(f"<b>Data:</b> {evento.data_inicio.strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Paragraph(f"<b>Local:</b> {evento.local}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # Dados do ingresso
    story.append(Paragraph(f"<b>Código do Ingresso:</b> {ingresso.id}", normal_style))
    story.append(Paragraph(f"<b>Lote:</b> {ingresso.pedido.lote.nome}", normal_style))
    story.append(Paragraph(f"<b>Valor:</b> R$ {ingresso.pedido.lote.preco:.2f}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # Dados do participante
    usuario = ingresso.pedido.usuario
    story.append(Paragraph(f"<b>Participante:</b> {usuario.nome}", normal_style))
    story.append(Paragraph(f"<b>CPF:</b> {usuario.cpf_cnpj}", normal_style))
    story.append(Paragraph(f"<b>Email:</b> {usuario.email}", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # QR Code (placeholder - será implementado depois)
    story.append(Paragraph("<b>Código QR para Check-in:</b>", normal_style))
    story.append(Paragraph(f"Hash: {ingresso.qr_code_hash}", normal_style))
    story.append(Spacer(1, 1*cm))

    # Instruções
    story.append(Paragraph("<b>Instruções:</b>", normal_style))
    story.append(Paragraph("• Apresente este ingresso na entrada do evento", normal_style))
    story.append(Paragraph("• O QR Code será escaneado para validação", normal_style))
    story.append(Paragraph("• Chegue com antecedência para evitar filas", normal_style))
    story.append(Spacer(1, 0.5*cm))

    # Status
    status_color = colors.green if ingresso.status.value == "ATIVO" else colors.red
    story.append(Paragraph(f"<b>Status:</b> <font color='{status_color}'>{ingresso.status.value}</font>", normal_style))

    # Rodapé
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("PampaTickets - Sistema de Gestão de Eventos", styles['Italic']))
    story.append(Paragraph("Gerado em: " + ingresso.created_at.strftime("%d/%m/%Y %H:%M"), styles['Italic']))

    # Gerar PDF
    doc.build(story)

    buffer.seek(0)
    return buffer


def gerar_pdf_certificado(ingresso: Ingresso) -> BinaryIO:
    """
    Gera um PDF de certificado de participação no evento.

    Args:
        ingresso: Instância do modelo Ingresso com status UTILIZADO

    Returns:
        Arquivo binário contendo o PDF do certificado
    """
    buffer = io.BytesIO()

    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=3*cm,
        leftMargin=3*cm,
        topMargin=4*cm,
        bottomMargin=3*cm
    )

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=50,
        alignment=1,  # Centralizado
        textColor=colors.darkblue
    )

    cert_style = ParagraphStyle(
        'CertText',
        parent=styles['Normal'],
        fontSize=16,
        alignment=1,  # Centralizado
        spaceAfter=20
    )

    # Conteúdo do certificado
    story = []

    # Título
    story.append(Paragraph("CERTIFICADO", title_style))

    # Texto do certificado
    evento = ingresso.pedido.lote.evento
    usuario = ingresso.pedido.usuario

    story.append(Paragraph("Certificamos que", cert_style))
    story.append(Paragraph(f"<b>{usuario.nome}</b>", cert_style))
    story.append(Paragraph("participou do evento", cert_style))
    story.append(Paragraph(f"<b>{evento.nome}</b>", cert_style))
    story.append(Paragraph(f"realizado em {evento.data_inicio.strftime('%d/%m/%Y')}", cert_style))
    story.append(Paragraph(f"no local: {evento.local}", cert_style))

    story.append(Spacer(1, 2*cm))

    # Data de emissão
    story.append(Paragraph(f"Certificado emitido em {ingresso.updated_at.strftime('%d/%m/%Y')}", cert_style))

    # Assinatura (placeholder)
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("_______________________________", cert_style))
    story.append(Paragraph("PampaTickets", cert_style))

    # Gerar PDF
    doc.build(story)

    buffer.seek(0)
    return buffer