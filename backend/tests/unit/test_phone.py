"""Normalização de telefone para E.164 (UC15)."""

import pytest

from app.core.phone import to_e164_br


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("54999998888", "+5554999998888"),       # celular 11 dígitos
        ("5433334444", "+555433334444"),          # fixo 10 dígitos
        ("(54) 99999-8888", "+5554999998888"),    # formatado
        ("+55 54 99999-8888", "+5554999998888"),  # já com +55 (13 díg)
        ("5554999998888", "+5554999998888"),      # 55 + 11 → strip do país
        # DDD 55 (Santa Maria/RS) NÃO é confundido com código do país:
        ("55999998888", "+5555999998888"),
        ("999998888", None),                      # 9 dígitos — curto demais
        ("123", None),
        ("", None),
        (None, None),
        ("abcdef", None),
    ],
)
def test_to_e164_br(entrada, esperado):
    assert to_e164_br(entrada) == esperado
