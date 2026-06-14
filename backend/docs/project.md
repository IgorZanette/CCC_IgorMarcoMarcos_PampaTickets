# project.md — Visão Geral do Projeto

## O que é o pampatickets

Plataforma digital de gerenciamento de eventos e venda de ingressos online, desenvolvida como projeto acadêmico na Universidade de Passo Fundo (UPF). Inspirada no Sympla, com identidade regional do Rio Grande do Sul.

Este repositório contém o **backend principal**, responsável por toda a lógica de negócio, autenticação e persistência de dados.

---

## Stack Técnica

| Responsabilidade | Tecnologia |
|---|---|
| Linguagem | Python |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Migrações | Alembic |
| Banco de dados | PostgreSQL |
| Autenticação | JWT via PyJWT — perfis: Organizador / Participante |
| Geração de PDF | ReportLab, assíncrono via `asyncio` |
| Armazenamento de arquivos | Supabase Storage |
| Gateway de pagamento | Asaas (sandbox para testes) |
| Notificações | Meta Cloud API — WhatsApp Business |
| Documentação de API | Swagger UI (nativa do FastAPI) |
| Gerenciamento de pacotes | uv |
| Testes | Pytest + HTTPX |

---

## Estrutura de Pastas

> Este documento lista **apenas o que existe hoje no código**. O UC15 (WhatsApp) ainda não está totalmente implementado — veja `roadmap.md` e `state.md` para o que está pendente.

```
backend/
├── alembic/                              # Migrations Alembic (versões geradas automaticamente)
├── app/
│   ├── api/
│   │   ├── deps.py                       # CurrentUser, OrganizadorUser, ParticipanteUser
│   │   ├── middleware/
│   │   │   └── logging.py                # LoggingMiddleware (loguru + request_id por request)
│   │   └── routes/
│   │       ├── auth.py                   # UC01 — cadastro, login, /me
│   │       ├── checkin.py                # UC04 — POST /checkin (OrganizadorUser, body JSON)
│   │       ├── cortesias.py              # UC06 — emitir/listar/obter/cancelar cortesia
│   │       ├── cupons.py                 # UC05 — CRUD + validar (preview do desconto)
│   │       ├── eventos.py                # UC02 — CRUD + publicar/encerrar/cancelar
│   │       ├── fotos.py                  # UC08 — galeria: publicar (organizador), listar (login), excluir
│   │       ├── ingressos.py              # ingressos do participante (/meus, /{id}) + listagem por evento do organizador
│   │       ├── lotes.py                  # UC03 — CRUD + ativar/desativar
│   │       ├── pedidos.py                # UC07 — criar, listar, detalhe, cancelar, reembolso
│   │       ├── relatorios.py             # UC14 — relatório financeiro: PDF (StreamingResponse) + resumo JSON
│   │       └── webhooks.py               # UC11 — receptor do Asaas
│   ├── core/
│   │   ├── config.py                     # Settings via pydantic-settings
│   │   ├── datetime_utils.py             # aware_utc() — normaliza naive → UTC tz-aware
│   │   ├── logging_config.py             # setup_logging() do loguru
│   │   └── validators.py                 # Mod 11 para CPF/CNPJ
│   ├── db/
│   │   ├── base.py                       # Base declarativa + import de todos os models
│   │   └── session.py                    # AsyncEngine, AsyncSession, init_db
│   ├── integrations/                     # Clientes HTTP de APIs externas — sem regra de negócio
│   │   ├── asaas/
│   │   │   ├── client.py                 # httpx.AsyncClient singleton + auth/timeout
│   │   │   ├── customers.py              # create_customer
│   │   │   ├── charges.py                # create_charge, delete_charge, refund_charge, get_pix_qrcode, get_boleto_identificacao
│   │   │   └── exceptions.py             # AsaasAPIError
│   │   └── supabase/
│   │       └── supabase_storage.py       # SupabaseStorage — upload de PDFs + fotos (UC08: upload/URL assinada/remover)
│   ├── models/
│   │   ├── usuario.py
│   │   ├── evento.py
│   │   ├── lote.py
│   │   ├── ingresso.py                   # pedido_item_id nullable (cortesia gera ingresso sem pedido)
│   │   ├── pedido.py                     # Pedido (com cupom_id, valor_desconto) + PedidoItem
│   │   ├── pagamento.py                  # Pagamento + Reembolso
│   │   ├── cupom.py                      # UC05 — UNIQUE(codigo, evento_id)
│   │   ├── cortesia.py                   # UC06 — relationships beneficiado/lote/ingresso
│   │   ├── checkin.py
│   │   ├── certificado.py
│   │   ├── relatorio.py                  # modelo só — UC14 NÃO persiste (relatório é regenerado sob demanda)
│   │   └── foto.py                       # FotoEvento (UC08) + CompraFoto (reservado p/ fase paga, sem uso)
│   ├── repositories/
│   │   ├── usuario_repo.py
│   │   ├── evento_repo.py
│   │   ├── lote_repo.py
│   │   ├── pedido_repo.py
│   │   ├── pagamento_repo.py
│   │   ├── reembolso_repo.py             # UC10
│   │   ├── ingresso_repo.py
│   │   ├── cupom_repo.py                 # UC05
│   │   ├── cortesia_repo.py              # UC06
│   │   ├── foto_repo.py                  # UC08 — CRUD da galeria de fotos
│   │   ├── checkin_repo.py               # UC04 — persiste linha em checkins
│   │   └── certificado_repo.py           # UC13 — persiste linha em certificados
│   ├── reports/
│   │   ├── ingresso_pdf.py               # gerar_pdf_ingresso (UC12) + gerar_pdf_certificado (UC13)
│   │   └── relatorio_pdf.py              # UC14 — DadosRelatorio/DadosLote + gerar_pdf_relatorio (tabelas ReportLab)
│   ├── schemas/
│   │   ├── _types.py                     # DatetimeUTC (assume UTC quando vem naive)
│   │   ├── usuario.py
│   │   ├── evento.py
│   │   ├── lote.py
│   │   ├── pedido.py                     # PedidoCreate aceita cupom_codigo opcional
│   │   ├── reembolso.py                  # UC10
│   │   ├── ingresso.py                   # IngressoResponse + IngressoOrganizadorResponse (listagem por evento)
│   │   ├── checkin.py                    # CheckinRequest (body) + CheckinResponse
│   │   ├── cupom.py                      # Create/Update/Response + ValidarRequest/Response
│   │   ├── cortesia.py                   # Create + Response (desnormaliza email/nome/lote)
│   │   ├── foto.py                       # UC08 — FotoResponse (URLs assinadas geradas no service)
│   │   └── relatorio.py                  # UC14 — RelatorioResumoResponse.from_dados (resumo JSON do dashboard)
│   ├── service/
│   │   ├── auth_service.py               # JWT + bcrypt
│   │   ├── evento_service.py
│   │   ├── lote_service.py
│   │   ├── pedido_service.py             # aplica cupom (cupom_codigo) e desconto no checkout
│   │   ├── pagamento_service.py          # criar_pagamento + processar_webhook + solicitar_reembolso
│   │   ├── cancelamento_service.py       # aplicar_cancelamento (manual + OVERDUE) — devolve cupom também
│   │   ├── ingresso_service.py           # criar_ingressos_para_pedido + PDFs + validar_checkin (auth)
│   │   ├── cupom_service.py              # UC05 — CRUD + validar_e_calcular_desconto
│   │   ├── cortesia_service.py           # UC06 — emitir/listar/obter/cancelar (atômico)
│   │   ├── foto_service.py               # UC08 — publicar (valida posse/tipo/tamanho) / listar / excluir
│   │   └── relatorio_service.py          # UC14 — montar_dados (5 queries) + gerar_relatorio (PDF)
│   └── main.py
├── docs/                                 # project.md, requirements.md, roadmap.md, state.md
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── CLAUDE.md
```

---

## Variáveis de Ambiente

Referência completa em `.env.example`. Resumo:

```env
# PostgreSQL (Docker Compose)
POSTGRES_USER=pampa
POSTGRES_PASSWORD=pampa
POSTGRES_DB=pampatickets

# Backend — FastAPI
ASYNC_DATABASE_URL=postgresql+asyncpg://pampa:pampa@localhost:5432/pampatickets

# JWT
SECRET_KEY=sua-chave-secreta-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Asaas (gateway de pagamento)
ASAAS_API_KEY=sua-api-key-asaas
ASAAS_BASE_URL_UAT=https://sandbox.asaas.com/api/v3
ASAAS_WEBHOOK_TOKEN=token-para-validar-webhooks

# Supabase Storage
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=sua-service-role-key
SUPABASE_BUCKET_INGRESSOS=ingressos
SUPABASE_BUCKET_CERTIFICADOS=certificados
SUPABASE_BUCKET_RELATORIOS=relatorios
SUPABASE_BUCKET_FOTOS=fotos   # UC08 — criar como bucket PRIVADO (acesso via URL assinada)

# Meta Cloud API — WhatsApp Business (UC15, ainda não implementado)
# META_WHATSAPP_TOKEN=seu-token-de-acesso
# META_PHONE_NUMBER_ID=id-do-numero-whatsapp
# META_VERIFY_TOKEN=token-de-verificacao-webhook
```

---

## Como Rodar

O projeto roda exclusivamente via Docker Compose. O `Makefile` na raiz expõe os comandos mais usados.

```bash
# Subir tudo (postgres + api). Migrations rodam automaticamente no lifespan via init_db.
make up

# Logs da API em tempo real
make logs-api

# Shell psql no banco
make shell-db

# Resetar o banco (DESTRUTIVO — apaga o volume postgres_data e re-cria do zero)
make db-reset

# Lista todos os comandos disponíveis
make help
```

Para criar uma nova migration manualmente:

```bash
make migration m="descrição da mudança"
make migrate            # aplica
make migrate-history    # histórico
```