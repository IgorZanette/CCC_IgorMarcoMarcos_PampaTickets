import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CheckinRequest(BaseModel):
    qr_code_hash: str = Field(..., min_length=10, examples=["abc123..."])


class CheckinResponse(BaseModel):
    checkin_id: uuid.UUID
    ingresso_id: uuid.UUID
    realizado_em: datetime
    evento_nome: str
    participante_nome: str
    certificado_url: str | None
