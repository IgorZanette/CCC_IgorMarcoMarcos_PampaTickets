"""Normalização de telefone brasileiro para o formato E.164 (+55DDNÚMERO),
exigido pela Meta Cloud API (UC15)."""

import re


def to_e164_br(celular: str | None) -> str | None:
    """Converte um celular/fixo brasileiro para E.164 (`+55DDNÚMERO`).

    Aceita formatos comuns — `54999998888`, `(54) 99999-8888`,
    `+55 54 99999-8888` — extraindo apenas os dígitos. Se o número já vier
    com o código do país (55), ele é removido antes da validação do DDD+número.

    Retorna `None` quando o resultado não tem 10 (fixo) ou 11 (celular)
    dígitos de DDD+número — o chamador trata como "sem telefone válido" e
    não envia, em vez de mandar um número malformado para a Meta.
    """
    digitos = re.sub(r"\D", "", celular or "")
    # Remove o código do país quando já presente (55 + 10 ou 11 dígitos).
    if len(digitos) in (12, 13) and digitos.startswith("55"):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        return None
    return f"+55{digitos}"
