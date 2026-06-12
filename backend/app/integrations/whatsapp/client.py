"""Cliente HTTP isolado da Meta Cloud API (WhatsApp Business).

Único ponto do código que fala com a Meta (regra do roadmap). Degrada
graciosamente: sem token/phone_number_id configurados, `send_template_message`
vira no-op — loga e retorna sem enviar, igual ao Supabase Storage quando não
configurado. Assim o fluxo principal nunca depende do WhatsApp.
"""

import httpx
from loguru import logger

from app.core.config import settings
from app.integrations.whatsapp.exceptions import WhatsAppAPIError

_client: httpx.AsyncClient | None = None


def esta_configurado() -> bool:
    """True quando há credenciais suficientes para enviar mensagens."""
    return bool(settings.META_WHATSAPP_TOKEN and settings.META_PHONE_NUMBER_ID)


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=f"https://graph.facebook.com/{settings.META_API_VERSION}",
            headers={
                "Authorization": f"Bearer {settings.META_WHATSAPP_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def send_template_message(
    to: str, template_name: str, params: list[str]
) -> dict | None:
    """Envia uma mensagem de template aprovado para `to` (E.164).

    `params` preenche os placeholders posicionais ({{1}}, {{2}}, ...) do corpo
    do template. Sem credenciais → no-op (retorna None). Erro da Meta →
    WhatsAppAPIError (capturado pelo whatsapp_service).
    """
    if not esta_configurado():
        logger.info(
            "WhatsApp não configurado — notificação '{}' ignorada (no-op)",
            template_name,
        )
        return None

    components = []
    if params:
        components.append(
            {
                "type": "body",
                "parameters": [{"type": "text", "text": str(p)} for p in params],
            }
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "pt_BR"},
            "components": components,
        },
    }

    response = await get_client().post(
        f"/{settings.META_PHONE_NUMBER_ID}/messages", json=payload
    )
    if response.is_error:
        raise WhatsAppAPIError(response.status_code, response.text)
    return response.json()
