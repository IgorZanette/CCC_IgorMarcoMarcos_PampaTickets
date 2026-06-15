"""Seed de eventos prontos para demonstração.

Cria (de forma idempotente) um organizador fixo e um conjunto de eventos
PUBLICADOS com nomes genéricos, cada um com 1-2 lotes de ingresso. Não gera
cortesias nem cupons.

Uso:
    uv run python -m app.db.seed
    # ou
    make seed
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.evento import Evento, StatusEvento
from app.models.lote import Lote, TipoLote
from app.models.usuario import PerfilUsuario, Usuario
from app.service import auth_service

# Organizador fixo da seed. CPF válido pelo Mod 11 (o @validates do model rejeita inválidos).
SEED_ORGANIZADOR_EMAIL = "seed@pampatickets.com"
SEED_ORGANIZADOR_CPF = "52998224725"
SEED_ORGANIZADOR_SENHA = "senha-secreta"

# Eventos genéricos. `dias` é o deslocamento (a partir de hoje) do início do evento.
SEED_EVENTOS = [
    {
        "nome": "Festival de Música ao Vivo",
        "descricao": "Uma noite com bandas locais e atrações nacionais.",
        "local": "Arena Pampa, Porto Alegre - RS",
        "dias": 30,
        "duracao_horas": 6,
    },
    {
        "nome": "Conferência de Tecnologia",
        "descricao": "Palestras e workshops sobre as últimas tendências em tecnologia.",
        "local": "Centro de Eventos FIERGS, Porto Alegre - RS",
        "dias": 45,
        "duracao_horas": 8,
    },
    {
        "nome": "Feira Gastronômica",
        "descricao": "Food trucks, chefs convidados e pratos típicos da região.",
        "local": "Parque Farroupilha, Porto Alegre - RS",
        "dias": 20,
        "duracao_horas": 10,
    },
    {
        "nome": "Peça de Teatro: O Espelho",
        "descricao": "Drama contemporâneo premiado, sessão única.",
        "local": "Teatro São Pedro, Porto Alegre - RS",
        "dias": 15,
        "duracao_horas": 2,
    },
    {
        "nome": "Workshop de Fotografia",
        "descricao": "Aprenda técnicas de composição e luz com profissionais.",
        "local": "Estúdio Central, Pelotas - RS",
        "dias": 25,
        "duracao_horas": 4,
    },
    {
        "nome": "Corrida Solidária 5K",
        "descricao": "Percurso pela orla com inscrição revertida para projetos sociais.",
        "local": "Orla do Guaíba, Porto Alegre - RS",
        "dias": 40,
        "duracao_horas": 3,
    },
    {
        "nome": "Exposição de Arte Contemporânea",
        "descricao": "Mostra coletiva de artistas gaúchos emergentes.",
        "local": "Santander Cultural, Porto Alegre - RS",
        "dias": 50,
        "duracao_horas": 8,
    },
    {
        "nome": "Show de Stand-up Comedy",
        "descricao": "Uma noite de humor com nomes da nova comédia.",
        "local": "Bar Opinião, Porto Alegre - RS",
        "dias": 35,
        "duracao_horas": 2,
    },
]


async def _get_or_create_organizador(db) -> Usuario:
    existente = await db.scalar(
        select(Usuario).where(Usuario.email == SEED_ORGANIZADOR_EMAIL)
    )
    if existente is not None:
        return existente

    organizador = Usuario(
        nome="Organizador Seed",
        email=SEED_ORGANIZADOR_EMAIL,
        cpf_cnpj=SEED_ORGANIZADOR_CPF,
        celular="54999407969",
        senha_hash=auth_service._hash_senha(SEED_ORGANIZADOR_SENHA),
        perfil=PerfilUsuario.ORGANIZADOR,
        ativo=True,
        email_verificado=True,
    )
    db.add(organizador)
    await db.commit()
    await db.refresh(organizador)
    return organizador


def _lotes_para(evento: Evento, agora: datetime) -> list[Lote]:
    """Inteira + Meia, com janela de venda aberta até o início do evento."""
    fim_venda = evento.data_inicio
    return [
        Lote(
            evento_id=evento.id,
            nome="1º Lote - Inteira",
            tipo=TipoLote.INTEIRA,
            preco=120.00,
            quantidade_total=200,
            quantidade_vendida=0,
            data_inicio_venda=agora - timedelta(days=1),
            data_fim_venda=fim_venda,
            ativo=True,
        ),
        Lote(
            evento_id=evento.id,
            nome="1º Lote - Meia",
            tipo=TipoLote.MEIA,
            preco=60.00,
            quantidade_total=100,
            quantidade_vendida=0,
            data_inicio_venda=agora - timedelta(days=1),
            data_fim_venda=fim_venda,
            ativo=True,
        ),
    ]


async def seed() -> None:
    agora = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        organizador = await _get_or_create_organizador(db)

        nomes_existentes = set(
            await db.scalars(
                select(Evento.nome).where(Evento.organizador_id == organizador.id)
            )
        )

        criados = 0
        for spec in SEED_EVENTOS:
            if spec["nome"] in nomes_existentes:
                print(f"  - já existe, pulando: {spec['nome']}")
                continue

            data_inicio = agora + timedelta(days=spec["dias"])
            data_fim = data_inicio + timedelta(hours=spec["duracao_horas"])
            evento = Evento(
                organizador_id=organizador.id,
                nome=spec["nome"],
                descricao=spec["descricao"],
                data_inicio=data_inicio,
                data_fim=data_fim,
                local=spec["local"],
                status=StatusEvento.PUBLICADO,
            )
            db.add(evento)
            await db.flush()  # garante evento.id para os lotes
            db.add_all(_lotes_para(evento, agora))
            criados += 1
            print(f"  + criado: {spec['nome']}")

        await db.commit()
        print(
            f"\nSeed concluída. {criados} evento(s) criado(s) "
            f"para o organizador {organizador.email}."
        )


if __name__ == "__main__":
    asyncio.run(seed())
