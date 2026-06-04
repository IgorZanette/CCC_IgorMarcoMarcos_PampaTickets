"""Testes unitários de app/core/datetime_utils.py::aware_utc."""

from datetime import datetime, timedelta, timezone

from app.core.datetime_utils import aware_utc


def test_naive_assume_utc():
    naive = datetime(2026, 1, 1, 12, 0, 0)
    result = aware_utc(naive)
    assert result.tzinfo == timezone.utc
    assert result.hour == 12


def test_aware_permanece_inalterado():
    tz = timezone(timedelta(hours=-3))
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=tz)
    result = aware_utc(aware)
    # Já é aware: a função devolve o mesmo objeto, sem converter o fuso.
    assert result is aware
    assert result.tzinfo == tz
