import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ingresso import Ingresso, StatusIngresso


class IngressoResponse(BaseModel):
    id: uuid.UUID
    qr_code_hash: str
    status: StatusIngresso
    pdf_url: str | None
    certificado_url: str | None = None
    emitido_em: datetime
    evento_nome: str
    evento_data_inicio: datetime
    evento_local: str
    lote_nome: str
    # Nulo para cortesias (ingresso sem pedido). Permite ao frontend acionar
    # o reembolso do pedido (UC10) a partir da tela "Meus ingressos".
    pedido_id: uuid.UUID | None
    # True quando o reembolso do pedido já foi solicitado mas o webhook do
    # Asaas ainda não confirmou o estorno (ingresso segue ATIVO nesse meio
    # tempo) — o frontend usa isso para não oferecer o botão de novo.
    reembolso_solicitado: bool = False

    model_config = {"from_attributes": True}

    @classmethod
    def from_ingresso(
        cls,
        ing: Ingresso,
        *,
        reembolso_solicitado: bool = False,
        certificado_url: str | None = None,
    ) -> "IngressoResponse":
        return cls(
            id=ing.id,
            qr_code_hash=ing.qr_code_hash,
            status=ing.status,
            pdf_url=ing.pdf_url,
            certificado_url=certificado_url,
            emitido_em=ing.emitido_em,
            evento_nome=ing.lote.evento.nome,
            evento_data_inicio=ing.lote.evento.data_inicio,
            evento_local=ing.lote.evento.local,
            lote_nome=ing.lote.nome,
            pedido_id=ing.pedido_item.pedido_id if ing.pedido_item else None,
            reembolso_solicitado=reembolso_solicitado,
        )


class IngressoOrganizadorResponse(BaseModel):
    id: uuid.UUID
    qr_code_hash: str
    status: StatusIngresso
    emitido_em: datetime
    lote_nome: str
    participante_nome: str
    participante_email: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_ingresso(cls, ing: Ingresso) -> "IngressoOrganizadorResponse":
        return cls(
            id=ing.id,
            qr_code_hash=ing.qr_code_hash,
            status=ing.status,
            emitido_em=ing.emitido_em,
            lote_nome=ing.lote.nome,
            participante_nome=ing.participante.nome,
            participante_email=ing.participante.email,
        )
