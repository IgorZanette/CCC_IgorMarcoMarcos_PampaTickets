"""Orquestra as notificações WhatsApp (UC15).

Único service que monta mensagens e fala (indiretamente) com a Meta — os
demais services apenas chamam `notificar_*` passando dados já carregados.

Regras do roadmap respeitadas aqui:
- Envio sempre via `BackgroundTasks` (nunca bloqueia o fluxo principal).
- Telefone normalizado para E.164 (`+55DDNÚMERO`); inválido → não envia.
- Falha de envio é best-effort: logada, nunca propagada.
- Toda mensagem usa template aprovado (notificação iniciada pelo negócio,
  fora da janela de 24h — não há caminho de mensagem livre).

Os nomes de template abaixo precisam existir e estar **aprovados** no Meta
Business Manager, com um placeholder de corpo por parâmetro posicional.
"""

from fastapi import BackgroundTasks
from loguru import logger

from app.core.config import settings
from app.core.phone import to_e164_br
from app.integrations.whatsapp import client as whatsapp_client
from app.integrations.whatsapp.exceptions import WhatsAppAPIError

TEMPLATE_PAGAMENTO_CONFIRMADO = "pagamento_confirmado"
TEMPLATE_CHECKIN_REALIZADO = "checkin_realizado"
TEMPLATE_EVENTO_CANCELADO = "evento_cancelado"


def _link_meus_ingressos() -> str:
    """Link para o participante acessar ingressos e certificados (PDF)."""
    return f"{settings.FRONTEND_URL.rstrip('/')}/meus-ingressos"


def notificar_pagamento_confirmado(
    background_tasks: BackgroundTasks | None,
    *,
    nome: str,
    telefone: str,
    evento_nome: str,
) -> None:
    """Compra confirmada — confirma e dá o link do ingresso PDF (roadmap)."""
    _agendar(
        background_tasks,
        telefone,
        TEMPLATE_PAGAMENTO_CONFIRMADO,
        [nome, evento_nome, _link_meus_ingressos()],
    )


def notificar_checkin(
    background_tasks: BackgroundTasks | None,
    *,
    nome: str,
    telefone: str,
    evento_nome: str,
) -> None:
    """Check-in realizado — dá o link do certificado PDF (roadmap)."""
    _agendar(
        background_tasks,
        telefone,
        TEMPLATE_CHECKIN_REALIZADO,
        [nome, evento_nome, _link_meus_ingressos()],
    )


def notificar_evento_cancelado(
    background_tasks: BackgroundTasks | None,
    *,
    nome: str,
    telefone: str,
    evento_nome: str,
) -> None:
    """Evento cancelado — avisa o participante sobre o reembolso."""
    _agendar(
        background_tasks,
        telefone,
        TEMPLATE_EVENTO_CANCELADO,
        [nome, evento_nome],
    )


def _agendar(
    background_tasks: BackgroundTasks | None,
    telefone: str,
    template: str,
    params: list[str],
) -> None:
    """Valida o telefone e agenda o envio para depois da resposta.

    `background_tasks` é None quando o service é chamado fora de um request
    (ex.: testes que exercitam o fluxo de pagamento direto) — nesse caso a
    notificação simplesmente não é agendada.
    """
    if background_tasks is None:
        return
    e164 = to_e164_br(telefone)
    if e164 is None:
        logger.warning(
            "WhatsApp: telefone inválido — notificação '{}' não enviada", template
        )
        return
    background_tasks.add_task(_enviar, to=e164, template=template, params=params)


async def _enviar(*, to: str, template: str, params: list[str]) -> None:
    """Executado em background. Best-effort: erro da Meta é logado, não sobe.

    Loga apenas o status HTTP — nunca o corpo do erro da Meta nem o destino:
    o `response.text` da Graph API pode conter o telefone do destinatário
    (PII/LGPD) em erros de número inválido/não-registrado.
    """
    try:
        await whatsapp_client.send_template_message(to, template, params)
    except WhatsAppAPIError as exc:
        logger.warning(
            "WhatsApp: falha ao enviar '{}' (HTTP {})", template, exc.status_code
        )
    except Exception:
        logger.exception("WhatsApp: erro inesperado ao enviar '{}'", template)
