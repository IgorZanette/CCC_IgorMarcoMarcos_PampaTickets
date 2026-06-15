.PHONY: help install dev build up down restart logs logs-api logs-db ps shell-api shell-db migrate migrate-down migrate-history migration seed test lint format destroy db-reset ngrok

DC = docker compose
BACKEND_DIR := backend

help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "  Docker"
	@echo "  ------"
	@echo "  build                Builda a imagem da API"
	@echo "  up                   Sobe todos os serviços em background"
	@echo "  down                 Para e remove os containers"
	@echo "  restart              Reinicia todos os serviços"
	@echo "  rebuild              Rebuilda todos os serviços"
	@echo "  logs                 Exibe logs de todos os serviços"
	@echo "  logs-api             Exibe logs da API"
	@echo "  logs-db              Exibe logs do banco de dados"
	@echo "  ps                   Lista os containers em execução"
	@echo "  shell-api            Abre shell no container da API"
	@echo "  shell-db             Abre psql no container do banco"
	@echo "  db-reset             Apaga o volume do banco e sobe tudo do zero (DESTRUTIVO)"
	@echo "  ngrok                Expõe a porta 8000 publicamente via ngrok (foreground)"
	@echo ""
	@echo "  Migrações"
	@echo "  ---------"
	@echo "  migrate              Aplica todas as migrações pendentes"
	@echo "  migrate-down         Reverte a última migração"
	@echo "  migrate-history      Exibe o histórico de migrações"
	@echo "  migration m=msg      Cria uma nova migração (ex: make migration m='add tabela X')"
	@echo "  seed                 Popula o banco com eventos de demonstração"
	@echo ""
	@echo "  Qualidade"
	@echo "  ---------"
	@echo "  test                 Executa os testes com pytest"
	@echo "  lint                 Verifica o código com ruff"
	@echo "  format               Formata o código com ruff"

# --- Docker ---

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart

rebuild:
	$(DC) down && $(DC) build

logs:
	$(DC) logs -f

logs-api:
	$(DC) logs -f api

logs-db:
	$(DC) logs -f db

ps:
	$(DC) ps

shell-api:
	$(DC) exec api /bin/sh

shell-db:
	$(DC) exec db psql -U $${POSTGRES_USER:-pampa} -d $${POSTGRES_DB:-pampatickets}

db-reset:
	$(DC) down -v
	$(DC) up -d

ngrok:
	ngrok http 8000

# --- Migrações ---

migrate:
	cd $(BACKEND_DIR) && uv run alembic upgrade head

migrate-down:
	cd $(BACKEND_DIR) && uv run alembic downgrade -1

migrate-history:
	cd $(BACKEND_DIR) && uv run alembic history --verbose

migration:
ifndef m
	$(error Informe a mensagem da migração: make migration m="sua mensagem")
endif
	cd $(BACKEND_DIR) && uv run alembic revision --autogenerate -m "$(m)"

seed:
	cd $(BACKEND_DIR) && uv run python -m app.db.seed

# --- Qualidade ---

test:
	cd $(BACKEND_DIR) && uv run pytest -v

lint:
	cd $(BACKEND_DIR) && uv run ruff check .

format:
	cd $(BACKEND_DIR) && uv run ruff format .
