# PampaTickets

Plataforma digital de gerenciamento de eventos e venda de ingressos online, desenvolvida como projeto acadêmico na Universidade de Passo Fundo (UPF). Inspirada no Sympla, com identidade regional do Rio Grande do Sul.

## Status do projeto

Backend em desenvolvimento ativo. Visão geral dos casos de uso:

| Status | Casos de uso |
|---|---|
| ✅ Implementado | UC01 Autenticação · UC02 Eventos · UC03 Lotes · UC04 Check-in · UC05 Cupons · UC06 Cortesias · UC07 Compra · UC09 Pagamento Asaas (Pix, boleto e cartão) · UC10 Reembolso · UC11 Webhooks · UC12 Ingresso PDF · UC13 Certificado PDF · UC14 Relatório financeiro |
| 🔶 Parcial | UC15 Notificações WhatsApp — draft estrutural pronto e testado (Meta mockada); falta credenciais/templates aprovados no Meta e o gatilho "véspera do evento". Pausado por decisão do time |
| ⏳ Pendente | UC08 Galeria de fotos (não iniciado, baixa prioridade) |

Detalhes do que está em andamento e do que mudou em cada sessão: [`backend/docs/state.md`](backend/docs/state.md).

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Banco de dados:** PostgreSQL
- **Frontend:** Vite (servido em container)
- **Autenticação:** JWT
- **Pagamentos:** Asaas (Pix, boleto, cartão de crédito)
- **Armazenamento:** Supabase Storage (PDFs)
- **Notificações:** WhatsApp via Meta Cloud API
- **Gerenciamento de pacotes:** uv

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose

> [uv](https://github.com/astral-sh/uv) é opcional — só necessário se você quiser rodar migrations ou `ruff` fora do container (`make migrate`, `make lint`, `make format`).

## Como rodar

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd pampatickets

# 2. Configure as variáveis de ambiente
cp .env.example .env
# edite .env com suas credenciais (Asaas, Supabase, JWT)

# 3. Build da imagem
make build

# 4. Sobe os serviços (API + Postgres + frontend)
make up
```

Após o `make up`:

- **API:** `http://localhost:8000`
- **Documentação Swagger:** `http://localhost:8000/docs`
- **Frontend:** `http://localhost:5173`

## Comandos úteis

| Comando | Descrição |
|---|---|
| `make build` | Builda a imagem da API |
| `make up` | Sobe todos os serviços em background |
| `make down` | Para e remove os containers |
| `make rebuild` | Para e rebuilda todos os serviços |
| `make logs-api` | Acompanha os logs da API em tempo real |
| `make shell-db` | Abre `psql` no banco de desenvolvimento |
| `make db-reset` | Apaga o volume do banco e sobe do zero (**destrutivo**, dev-only) |
| `make migrate` | Aplica migrações pendentes |
| `make migration m="mensagem"` | Cria uma nova migração |
| `make test` | Executa os testes |
| `make lint` | Verifica o código com ruff |

> Lista completa: `make help`.

## Documentação interna

A documentação técnica do backend vive em [`backend/docs/`](backend/docs/):

| Arquivo | Conteúdo |
|---|---|
| [`project.md`](backend/docs/project.md) | Visão geral, stack e estrutura de pastas |
| [`requirements.md`](backend/docs/requirements.md) | Regras de arquitetura, domínio e camadas |
| [`roadmap.md`](backend/docs/roadmap.md) | Ordem de implementação e integrações externas |
| [`state.md`](backend/docs/state.md) | Estado atual e histórico de decisões por sessão |
