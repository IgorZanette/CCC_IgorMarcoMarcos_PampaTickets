from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.service.pagamento_service import processar_webhook

router = APIRouter()


@router.post("/webhooks/asaas", tags=["Webhooks"])
async def asaas_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Webhook para receber notificações do Asaas sobre pagamentos.

    O Asaas envia notificações quando:
    - PAYMENT_CONFIRMED: Pagamento confirmado
    - PAYMENT_RECEIVED: Pagamento recebido
    - PAYMENT_OVERDUE: Pagamento vencido
    - PAYMENT_REFUNDED: Pagamento estornado
    """
    # Validar token de autenticação do webhook (se configurado)
    if settings.ASAAS_WEBHOOK_TOKEN:
        asaas_token = request.headers.get("asaas-access-token")
        if not asaas_token or asaas_token != settings.ASAAS_WEBHOOK_TOKEN:
            raise HTTPException(status_code=401, detail="Token de webhook inválido")

    # Obter dados do webhook
    try:
        data: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    # Validar estrutura básica do webhook
    if "event" not in data or "payment" not in data:
        raise HTTPException(status_code=400, detail="Estrutura de webhook inválida")

    evento = data["event"]
    payment_id = data["payment"]["id"]

    # Processar o webhook
    try:
        await processar_webhook(db, evento=evento, payment_id=payment_id)
    except Exception as e:
        # Log do erro (já é feito pelo middleware de logging)
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")

    # Retornar sucesso para o Asaas
    return {"status": "ok"}