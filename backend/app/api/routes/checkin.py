from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.service.ingresso_service import validar_checkin

router = APIRouter()


@router.post("/checkin", tags=["Check-in"])
async def checkin_ingresso(
    *,
    db: AsyncSession = Depends(get_db),
    qr_code_hash: str,
) -> dict[str, Any]:
    """
    Valida um ingresso via QR Code e marca como utilizado.

    Args:
        qr_code_hash: Hash do QR Code do ingresso

    Returns:
        Dados do ingresso validado e URL do certificado
    """
    resultado = await validar_checkin(db, qr_code_hash)

    if resultado is None:
        raise HTTPException(
            status_code=400,
            detail="Ingresso inválido, expirado ou já utilizado"
        )

    return {
        "status": "success",
        "message": "Check-in realizado com sucesso",
        "data": resultado
    }