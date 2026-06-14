"""Identidade visual compartilhada pelos PDFs (ingresso, certificado, relatório).

Centraliza a paleta da marca, o logo e a geração do QR Code real, para que os
três relatórios tenham aparência consistente com o frontend.
"""

import io
from pathlib import Path
from typing import BinaryIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage

# === Paleta da marca (espelha as variáveis --pt-* do frontend) ===
VERDE = colors.HexColor("#2d6b3f")  # verde-pampa profundo
VERDE_CLARO = colors.HexColor("#7eb86b")
VERDE_SOFT = colors.HexColor("#e8f0e8")
GOLD = colors.HexColor("#c89b3c")
GOLD_CLARO = colors.HexColor("#e8c547")
TEXTO = colors.HexColor("#0e1410")
TEXTO_DIM = colors.HexColor("#6b7770")
BORDA = colors.HexColor("#e5e7e2")
BORDEAUX = colors.HexColor("#8b1e2a")

# === Tema escuro (espelha [data-theme="dark"] do frontend — o visual usado
# nos PDFs, para parecerem um "resumo do dashboard") ===
BG = colors.HexColor("#0b0d0c")
BG_CARD = colors.HexColor("#15181a")
BG_CARD_2 = colors.HexColor("#1c2024")
BORDA_DARK = colors.HexColor("#262b2f")
TEXTO_LIGHT = colors.HexColor("#f5f6f7")
TEXTO_DIM_DARK = colors.HexColor("#8a9199")
ACCENT = colors.HexColor("#7eb86b")  # verde-pampa (accent no dark)
ACCENT_SOFT = colors.HexColor("#1d2a1f")  # fundo verde bem escuro p/ realces

# === Tema claro — exclusivo para o certificado ===
CERT_BG = colors.HexColor("#fffef8")          # creme suave
CERT_BORDA_EXT = colors.HexColor("#2d6b3f")   # verde pampa (borda externa)
CERT_BORDA_INT = colors.HexColor("#c89b3c")   # dourado (borda interna)
CERT_TEXTO = colors.HexColor("#1a2e1e")       # verde muito escuro p/ corpo
CERT_TEXTO_DIM = colors.HexColor("#5a6b5c")   # verde-cinza p/ textos menores

_LOGO_PATH = Path(__file__).resolve().parent.parent / "static" / "logo.png"


def pintar_fundo_dark(canvas, doc) -> None:
    """Pinta a página inteira com o fundo escuro da plataforma.

    Passado como onFirstPage/onLaterPages no build() — roda antes dos flowables,
    ficando atrás do conteúdo.
    """
    canvas.saveState()
    largura, altura = doc.pagesize
    canvas.setFillColor(BG)
    canvas.rect(0, 0, largura, altura, fill=1, stroke=0)
    canvas.restoreState()


def logo_flowable(width_cm: float = 3.5) -> RLImage | None:
    """Logo da marca como flowable do ReportLab, mantendo a proporção original.

    Devolve None se o arquivo não existir — os PDFs degradam para só o texto.
    """
    if not _LOGO_PATH.exists():
        return None
    reader = ImageReader(str(_LOGO_PATH))
    largura_px, altura_px = reader.getSize()
    largura = width_cm * cm
    altura = largura * altura_px / largura_px
    return RLImage(str(_LOGO_PATH), width=largura, height=altura)


def gerar_qrcode_image(dados: str) -> BinaryIO:
    """Gera um QR Code PNG real (escaneável) a partir do conteúdo informado."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(dados)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0e1410", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def qrcode_flowable(dados: str, size_cm: float = 4.5) -> RLImage:
    """QR Code já pronto como flowable, no tamanho indicado."""
    buffer = gerar_qrcode_image(dados)
    lado = size_cm * cm
    return RLImage(buffer, width=lado, height=lado)


def pintar_fundo_certificado(canvas, doc) -> None:
    """Fundo creme com borda dupla decorativa para o certificado (tema claro)."""
    canvas.saveState()
    largura, altura = doc.pagesize

    canvas.setFillColor(CERT_BG)
    canvas.rect(0, 0, largura, altura, fill=1, stroke=0)

    margem_ext = 1.0 * cm
    canvas.setStrokeColor(CERT_BORDA_EXT)
    canvas.setLineWidth(3)
    canvas.rect(margem_ext, margem_ext, largura - 2 * margem_ext, altura - 2 * margem_ext, fill=0, stroke=1)

    margem_int = margem_ext + 0.4 * cm
    canvas.setStrokeColor(CERT_BORDA_INT)
    canvas.setLineWidth(1)
    canvas.rect(margem_int, margem_int, largura - 2 * margem_int, altura - 2 * margem_int, fill=0, stroke=1)

    canvas.restoreState()
