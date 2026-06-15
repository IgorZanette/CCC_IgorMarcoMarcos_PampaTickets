# PampaTickets

Plataforma digital de gerenciamento de eventos e venda de ingressos online, desenvolvida como projeto acadêmico na Universidade de Passo Fundo (UPF). Inspirada no Sympla, com identidade regional do Rio Grande do Sul.

## Funcionalidades

- Cadastro e autenticação de organizadores e participantes (JWT)
- Criação e publicação de eventos, com lotes de ingressos (inteira, meia e promocional)
- Compra de ingressos online com pagamento via Pix, boleto e cartão de crédito
- Cupons de desconto e emissão de cortesias
- Reembolso de pedidos
- Check-in de participantes no evento
- Geração de ingressos e certificados em PDF
- Relatório financeiro por evento

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Banco de dados:** PostgreSQL
- **Frontend:** React 19, TypeScript, Vite (SPA), react-router-dom, axios, CSS Modules
- **Autenticação:** JWT
- **Pagamentos:** Asaas (Pix, boleto, cartão de crédito)
- **Armazenamento:** Supabase Storage (PDFs)
- **Notificações:** WhatsApp via Meta Cloud API
- **Testes:** pytest (backend) · Vitest (frontend)
- **Gerenciamento de pacotes:** uv (backend) · npm (frontend)

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
| `make seed` | Cria registros de testes no banco de dados |
| `make test` | Executa os testes |
| `make lint` | Verifica o código com ruff |

> Lista completa: `make help`.

## Documentação interna

A documentação técnica do **backend** vive em [`backend/docs/`](backend/docs/):

| Arquivo | Conteúdo |
|---|---|
| [`project.md`](backend/docs/project.md) | Visão geral, stack e estrutura de pastas |
| [`requirements.md`](backend/docs/requirements.md) | Regras de arquitetura, domínio e camadas |
| [`roadmap.md`](backend/docs/roadmap.md) | Ordem de implementação e integrações externas |
| [`state.md`](backend/docs/state.md) | Estado atual e histórico de decisões por sessão |

A documentação técnica do **frontend** vive em [`frontend/docs/`](frontend/docs/):

| Arquivo | Conteúdo |
|---|---|
| [`project.md`](frontend/docs/project.md) | Visão geral, stack e estrutura de pastas |
| [`requirements.md`](frontend/docs/requirements.md) | Regras de arquitetura, padrões de UI e convenções |
| [`roadmap.md`](frontend/docs/roadmap.md) | Prioridades de implementação e telas pendentes |
| [`state.md`](frontend/docs/state.md) | Estado atual e histórico de decisões por sessão |
