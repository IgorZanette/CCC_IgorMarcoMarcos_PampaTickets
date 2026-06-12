from fastapi import APIRouter, BackgroundTasks

from app.api.deps import DbDep, OrganizadorUser
from app.schemas.checkin import CheckinRequest, CheckinResponse
from app.service.ingresso_service import validar_checkin

router = APIRouter(tags=["Check-in"])


@router.post("/checkin", response_model=CheckinResponse)
async def checkin_ingresso(
    data: CheckinRequest,
    db: DbDep,
    organizador: OrganizadorUser,
    background_tasks: BackgroundTasks,
):
    return await validar_checkin(
        db,
        qr_code_hash=data.qr_code_hash,
        usuario=organizador,
        background_tasks=background_tasks,
    )
