"""Limiter compartilhado (slowapi) para proteger endpoints sensíveis a abuso.

Chave por IP de origem. O wiring (state + handler) fica em app.main; as rotas
aplicam limites via @limiter.limit("N/minute").
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
