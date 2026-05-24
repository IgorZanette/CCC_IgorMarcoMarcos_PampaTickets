import uuid
from datetime import datetime

from pydantic import BaseModel, Field, computed_field, model_validator

from app.models.cupom import TipoDesconto
from app.schemas._types import DatetimeUTC


class CupomCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=50, examples=["PROMO10"])
    tipo_desconto: TipoDesconto = Field(..., examples=["PERCENTUAL"])
    valor_desconto: float = Field(..., gt=0, examples=[10.0])
    quantidade_maxima: int | None = Field(None, ge=1, examples=[100])
    valido_ate: DatetimeUTC = Field(..., examples=["2026-12-31T23:59:00"])
    ativo: bool = Field(True, examples=[True])

    @model_validator(mode="after")
    def validar_valor_percentual(self) -> "CupomCreate":
        if self.tipo_desconto == TipoDesconto.PERCENTUAL and self.valor_desconto > 100:
            raise ValueError("valor_desconto percentual não pode ser maior que 100.")
        return self


class CupomUpdate(BaseModel):
    tipo_desconto: TipoDesconto | None = None
    valor_desconto: float | None = Field(None, gt=0)
    quantidade_maxima: int | None = Field(None, ge=1)
    valido_ate: DatetimeUTC | None = None
    ativo: bool | None = None

    @model_validator(mode="after")
    def validar_valor_percentual(self) -> "CupomUpdate":
        if (
            self.tipo_desconto == TipoDesconto.PERCENTUAL
            and self.valor_desconto is not None
            and self.valor_desconto > 100
        ):
            raise ValueError("valor_desconto percentual não pode ser maior que 100.")
        return self


class CupomResponse(BaseModel):
    id: uuid.UUID
    evento_id: uuid.UUID
    codigo: str
    tipo_desconto: TipoDesconto
    valor_desconto: float
    quantidade_maxima: int | None
    quantidade_usada: int
    valido_ate: datetime
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def quantidade_disponivel(self) -> int | None:
        if self.quantidade_maxima is None:
            return None
        return self.quantidade_maxima - self.quantidade_usada


class CupomValidarRequest(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=50, examples=["PROMO10"])
    valor_base: float = Field(..., gt=0, examples=[200.0])


class CupomValidarResponse(BaseModel):
    cupom_id: uuid.UUID
    codigo: str
    tipo_desconto: TipoDesconto
    valor_desconto_aplicado: float
    valor_final: float
