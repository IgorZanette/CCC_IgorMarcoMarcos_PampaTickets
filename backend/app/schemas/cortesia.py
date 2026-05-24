import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.cortesia import Cortesia


class CortesiaCreate(BaseModel):
    lote_id: uuid.UUID
    email_beneficiado: EmailStr = Field(..., examples=["participante@test.com"])
    motivo: str | None = Field(
        None, max_length=500, examples=["Patrocinador da edição 2026"]
    )


class CortesiaResponse(BaseModel):
    id: uuid.UUID
    evento_id: uuid.UUID
    lote_id: uuid.UUID
    beneficiado_id: uuid.UUID
    emitida_por: uuid.UUID
    ingresso_id: uuid.UUID | None
    emitida_em: datetime
    beneficiado_email: str
    beneficiado_nome: str
    lote_nome: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_cortesia(cls, cortesia: Cortesia) -> "CortesiaResponse":
        return cls(
            id=cortesia.id,
            evento_id=cortesia.evento_id,
            lote_id=cortesia.lote_id,
            beneficiado_id=cortesia.beneficiado_id,
            emitida_por=cortesia.emitida_por,
            ingresso_id=cortesia.ingresso_id,
            emitida_em=cortesia.emitida_em,
            beneficiado_email=cortesia.beneficiado.email,
            beneficiado_nome=cortesia.beneficiado.nome,
            lote_nome=cortesia.lote.nome,
        )
