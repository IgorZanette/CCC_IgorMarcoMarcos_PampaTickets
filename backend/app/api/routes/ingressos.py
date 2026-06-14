import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OrganizadorUser, ParticipanteUser
from app.db.session import get_db
from app.repositories import certificado_repo, evento_repo, ingresso_repo, reembolso_repo
from app.schemas.ingresso import IngressoOrganizadorResponse, IngressoResponse

router = APIRouter(tags=["Ingressos"])


@router.get(
    "/organizador/eventos/{evento_id}/ingressos",
    response_model=list[IngressoOrganizadorResponse],
)
async def listar_ingressos_do_evento(
    evento_id: uuid.UUID,
    organizador: OrganizadorUser,
    db: AsyncSession = Depends(get_db),
) -> list[IngressoOrganizadorResponse]:
    evento = await evento_repo.get_by_id(db, evento_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    if evento.organizador_id != organizador.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é o organizador deste evento.",
        )
    ingressos = await ingresso_repo.list_by_evento(db, evento_id)
    return [IngressoOrganizadorResponse.from_ingresso(i) for i in ingressos]


@router.get("/ingressos/meus", response_model=list[IngressoResponse])
async def listar_meus_ingressos(
    participante: ParticipanteUser,
    db: AsyncSession = Depends(get_db),
) -> list[IngressoResponse]:
    ingressos = await ingresso_repo.list_by_participante(db, participante.id)
    pedido_ids = {
        i.pedido_item.pedido_id for i in ingressos if i.pedido_item is not None
    }
    reembolsados = await reembolso_repo.pedido_ids_com_reembolso(db, pedido_ids)
    cert_urls = await certificado_repo.get_urls_by_ingresso_ids(
        db, [i.id for i in ingressos]
    )
    return [
        IngressoResponse.from_ingresso(
            i,
            reembolso_solicitado=(
                i.pedido_item is not None
                and i.pedido_item.pedido_id in reembolsados
            ),
            certificado_url=cert_urls.get(i.id),
        )
        for i in ingressos
    ]


@router.get("/ingressos/{ingresso_id}", response_model=IngressoResponse)
async def obter_ingresso(
    ingresso_id: uuid.UUID,
    participante: ParticipanteUser,
    db: AsyncSession = Depends(get_db),
) -> IngressoResponse:
    ingresso = await ingresso_repo.get_with_relations(db, str(ingresso_id))
    if ingresso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingresso não encontrado.",
        )
    if ingresso.participante_id != participante.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este ingresso.",
        )
    reembolsados = (
        await reembolso_repo.pedido_ids_com_reembolso(
            db, [ingresso.pedido_item.pedido_id]
        )
        if ingresso.pedido_item is not None
        else set()
    )
    return IngressoResponse.from_ingresso(
        ingresso, reembolso_solicitado=bool(reembolsados)
    )
