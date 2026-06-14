from datetime import date

from app.integrations.asaas.client import get_client
from app.integrations.asaas.exceptions import AsaasAPIError


async def get_pix_qrcode(*, charge_id: str) -> dict:
    route = f"/payments/{charge_id}/pixQrCode"

    response = await get_client().get(route)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)
    return response.json()


async def get_charge(*, charge_id: str) -> dict:
    route = f"/payments/{charge_id}"

    response = await get_client().get(route)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)
    return response.json()


async def get_boleto_identificacao(*, charge_id: str) -> dict:
    """Linha digitável e código de barras do boleto (rota específica de boleto).

    Retorna `{"identificationField": "...", "barCode": "...", "nossoNumero": "..."}`.
    O PDF do boleto (`bankSlipUrl`) já vem no response do `create_charge`.
    """
    route = f"/payments/{charge_id}/identificationField"

    response = await get_client().get(route)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)
    return response.json()


async def create_charge(
    *,
    customer_id: str,
    billing_type: str,
    value: float,
    due_date: date,
    external_reference: str,
) -> dict:
    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": value,
        "dueDate": due_date.isoformat(),
        "externalReference": external_reference,
    }
    response = await get_client().post("/payments", json=payload)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)
    return response.json()


async def delete_charge(*, charge_id: str) -> bool:
    route = f"/payments/{charge_id}"

    response = await get_client().delete(route)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)

    return response.json()["deleted"]  # caso não encontrar o campo vai estourar um erro


async def refund_charge(*, charge_id: str, value: float | None = None) -> dict:
    """
    Solicita reembolso de uma cobrança no Asaas.
    `value` opcional permite reembolso parcial; sem ele, o Asaas reembolsa o total.
    """
    payload = {"value": value} if value is not None else {}
    route = f"/payments/{charge_id}/refund"

    response = await get_client().post(route, json=payload)
    if response.is_error:
        raise AsaasAPIError(response.status_code, response.text)
    return response.json()
