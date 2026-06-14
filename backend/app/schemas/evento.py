import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.evento import StatusEvento
from app.schemas._types import DatetimeUTC


class EventoCreate(BaseModel):
    nome: str = Field(
        ..., min_length=3, max_length=255, examples=["Festival Pampa 2026"]
    )
    descricao: str | None = Field(
        None, examples=["Festival de música ao ar livre na orla do Guaíba"]
    )
    data_inicio: DatetimeUTC = Field(..., examples=["2026-12-31T20:00:00"])
    data_fim: DatetimeUTC = Field(..., examples=["2026-12-31T23:59:00"])
    local: str = Field(
        ...,
        min_length=3,
        max_length=500,
        examples=["Parque Farroupilha, Porto Alegre"],
    )
    endereco_completo: str | None = Field(None, max_length=500)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    @model_validator(mode="after")
    def validar_periodo(self) -> "EventoCreate":
        if self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio.")
        return self


class EventoUpdate(BaseModel):
    nome: str | None = Field(None, min_length=3, max_length=255)
    descricao: str | None = None
    data_inicio: DatetimeUTC | None = None
    data_fim: DatetimeUTC | None = None
    local: str | None = Field(None, min_length=3, max_length=500)
    endereco_completo: str | None = Field(None, max_length=500)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    @model_validator(mode="after")
    def validar_periodo(self) -> "EventoUpdate":
        if (
            self.data_inicio is not None
            and self.data_fim is not None
            and self.data_fim <= self.data_inicio
        ):
            raise ValueError("data_fim deve ser posterior a data_inicio.")
        return self


class EventoResponse(BaseModel):
    id: uuid.UUID
    organizador_id: uuid.UUID
    nome: str
    descricao: str | None
    data_inicio: datetime
    data_fim: datetime
    local: str
    endereco_completo: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: StatusEvento
    criado_em: datetime

    model_config = {"from_attributes": True}
