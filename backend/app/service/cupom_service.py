import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import aware_utc
from app.models.cupom import Cupom, TipoDesconto
from app.models.usuario import Usuario
from app.repositories import cupom_repo, evento_repo
from app.schemas.cupom import CupomCreate, CupomUpdate


async def criar(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
    data: CupomCreate,
) -> Cupom:
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

    cupom = Cupom(
        evento_id=evento.id,
        codigo=data.codigo,
        tipo_desconto=data.tipo_desconto,
        valor_desconto=data.valor_desconto,
        quantidade_maxima=data.quantidade_maxima,
        valido_ate=data.valido_ate,
        ativo=data.ativo,
    )
    try:
        return await cupom_repo.create(db, cupom)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um cupom com código '{data.codigo}' neste evento.",
        )


async def listar_por_evento(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> list[Cupom]:
    await _validar_ownership_evento(db, organizador, evento_id)
    return await cupom_repo.list_by_evento(db, evento_id)


async def obter(db: AsyncSession, organizador: Usuario, cupom_id: uuid.UUID) -> Cupom:
    cupom, _ = await _obter_cupom_proprio(db, organizador, cupom_id)
    return cupom


async def editar(
    db: AsyncSession,
    organizador: Usuario,
    cupom_id: uuid.UUID,
    data: CupomUpdate,
) -> Cupom:
    cupom, _ = await _obter_cupom_proprio(db, organizador, cupom_id)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return cupom

    nova_qtd_max = campos.get("quantidade_maxima", cupom.quantidade_maxima)
    if nova_qtd_max is not None and nova_qtd_max < cupom.quantidade_usada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "quantidade_maxima não pode ser inferior à quantidade já usada "
                f"({cupom.quantidade_usada})."
            ),
        )

    # Valida a coerência tipo×valor considerando o estado final (merge), não só o
    # payload — ex.: trocar para PERCENTUAL mantendo um valor fixo > 100.
    novo_tipo = campos.get("tipo_desconto", cupom.tipo_desconto)
    novo_valor = campos.get("valor_desconto", cupom.valor_desconto)
    if novo_tipo == TipoDesconto.PERCENTUAL and float(novo_valor) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="valor_desconto percentual não pode ser maior que 100.",
        )

    return await cupom_repo.update(db, cupom, **campos)


async def excluir(db: AsyncSession, organizador: Usuario, cupom_id: uuid.UUID) -> None:
    cupom, _ = await _obter_cupom_proprio(db, organizador, cupom_id)
    if cupom.quantidade_usada > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não é possível deletar um cupom já utilizado. "
                "Desative-o via PUT /api/cupons/{id} com ativo=false."
            ),
        )
    await cupom_repo.delete(db, cupom)


async def validar_e_calcular_desconto(
    db: AsyncSession,
    evento_id: uuid.UUID,
    codigo: str,
    valor_base: Decimal | float,
    *,
    for_update: bool = False,
) -> tuple[Cupom, Decimal]:
    """
    Valida o cupom para o evento e calcula o valor de desconto a aplicar.
    Levanta HTTPException em qualquer cenário inválido.
    Não persiste nem incrementa quantidade_usada — quem chama decide.

    `for_update=True` (usado na criação de pedido) trava a linha do cupom para
    serializar a checagem de esgotamento sob concorrência.
    """
    cupom = await cupom_repo.get_by_codigo_and_evento(
        db, codigo, evento_id, for_update=for_update
    )
    if cupom is None or not cupom.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cupom não encontrado ou inativo para este evento.",
        )

    agora = datetime.now(timezone.utc)
    if aware_utc(cupom.valido_ate) < agora:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cupom expirado.",
        )

    if (
        cupom.quantidade_maxima is not None
        and cupom.quantidade_usada >= cupom.quantidade_maxima
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cupom esgotado.",
        )

    base = Decimal(str(valor_base))
    if cupom.tipo_desconto == TipoDesconto.PERCENTUAL:
        valor_desconto = base * (cupom.valor_desconto / Decimal(100))
    else:  # VALOR_FIXO
        valor_desconto = min(cupom.valor_desconto, base)

    return cupom, valor_desconto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def _validar_ownership_evento(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> None:
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


async def _obter_cupom_proprio(
    db: AsyncSession, organizador: Usuario, cupom_id: uuid.UUID
) -> tuple[Cupom, uuid.UUID]:
    cupom = await cupom_repo.get_by_id(db, cupom_id)
    if cupom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cupom não encontrado.",
        )
    await _validar_ownership_evento(db, organizador, cupom.evento_id)
    return cupom, cupom.evento_id
