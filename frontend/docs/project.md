# project.md — Visão Geral do Frontend

## O que é o pampatickets (frontend)

Interface web do pampatickets — plataforma de gerenciamento de eventos e venda de ingressos online (projeto acadêmico UPF, inspirado no Sympla com identidade regional do RS).

Este diretório contém o **frontend SPA** em React + TypeScript que consome o backend FastAPI exposto em `http://localhost:8000/api`. Dois fluxos principais coexistem, em rotas **flat** (estilo Ticketmaster) — só o organizador tem prefixo próprio:

- **Vitrine + Participante** (tema escuro, sem prefixo): `/eventos`, `/eventos/:id`, `/eventos/:id/checkout`, `/meus-ingressos`, `/inicio`.
- **Organizador** (tema claro, prefixo `/organizador`): `/organizador` (dashboard), `/organizador/evento`, `/organizador/lotes`, `/organizador/checkin`, `/organizador/financeiro`, etc.

---

## Stack Técnica

| Responsabilidade | Tecnologia |
|---|---|
| Linguagem | TypeScript |
| Biblioteca UI | React 19 |
| Bundler / dev server | Vite 8 |
| Roteamento | react-router-dom v7 |
| HTTP client | axios |
| Estilos | CSS Modules (`*.module.css`) |
| Estado de auth | `localStorage` + `CustomEvent` (hook próprio, sem Context) |
| Linter | ESLint 10 + typescript-eslint |
| Gerenciamento de pacotes | npm |
| Containerização | Docker (node:22-alpine) — porta `5173` |

---

## Estrutura de Pastas

> Este documento lista **apenas o que existe hoje no código**. Telas/fluxos ainda não implementados não estão na árvore — veja `roadmap.md` e `state.md` para o pendente.

```
frontend/
├── public/                                # Assets estáticos servidos como estão (favicon etc.)
├── src/
│   ├── api/                               # Camada de comunicação com o backend (FastAPI)
│   │   ├── client.ts                      # axios singleton + interceptor de JWT (localStorage)
│   │   ├── auth.ts                        # login, cadastro, logout, tipos Usuario/Perfil
│   │   ├── eventos.ts                     # CRUD de eventos + gradientFor(id) determinístico
│   │   ├── lotes.ts                       # listar/criar/editar/ativar/deletar lotes (UC03)
│   │   ├── pedidos.ts                     # criar pedido, listar/cancelar/reembolsar (UC07/UC09/UC10)
│   │   ├── ingressos.ts                   # GET /api/ingressos/meus, /api/ingressos/{id} (UC07/UC12)
│   │   └── checkin.ts                     # POST /api/checkin (UC04 — organizador)
│   ├── components/                        # Componentes reutilizáveis entre páginas
│   │   ├── DateBlock.tsx                  # Bloco de data destacado (dia/mês/semana)
│   │   ├── EventCard.tsx                  # Card de evento (grid e listas)
│   │   ├── Logo.tsx                       # Logotipo pampatickets
│   │   ├── MetricCard.tsx                 # Card de métrica (dashboard organizador)
│   │   ├── PageHeader.tsx                 # Cabeçalho padrão de página interna
│   │   ├── ProgressBar.tsx                # Barra de progresso (ocupação de lote etc.)
│   │   └── StatusPill.tsx                 # Pílula colorida de status (pedido/ingresso)
│   ├── layouts/                           # Cascas de layout por persona
│   │   ├── ParticipantLayout.tsx          # Tema escuro — envolve a vitrine pública e as telas do participante
│   │   └── OrganizerLayout.tsx            # Tema claro — envolve as rotas sob /organizador
│   ├── lib/                               # Utilitários puros (sem componentes React)
│   │   ├── auth-store.ts                  # useCurrentUser + setStoredUser (sync via CustomEvent)
│   │   ├── active-event.ts                # useActiveEvent — id do evento ativo do organizador em localStorage
│   │   ├── errors.ts                      # extractErrorMessage — traduz erros do FastAPI/axios
│   │   └── format.ts                      # money, dateShort, dateLong, dateFull, formatCpfCnpj, formatCelular
│   ├── pages/                             # Telas (uma pasta por persona + auth)
│   │   ├── auth/                          # Rotas /login e /cadastro
│   │   │   ├── AuthShell.tsx              # Layout compartilhado das telas de login/cadastro
│   │   │   ├── LoginPage.tsx
│   │   │   ├── CadastroPage.tsx
│   │   │   └── forms.module.css           # Estilos compartilhados de formulários de auth
│   │   ├── participante/                  # Telas da vitrine pública e do participante (sem prefixo)
│   │   │   ├── HomePage.tsx               # /inicio — vitrine pós-login (destaques)
│   │   │   ├── SearchPage.tsx             # /eventos — busca e filtros
│   │   │   ├── EventoPage.tsx             # /eventos/:id — detalhe do evento
│   │   │   ├── CheckoutPage.tsx           # /eventos/:id/checkout — compra (UC07)
│   │   │   ├── TicketsPage.tsx            # /eventos/:id/ingressos — confirmação pós-compra
│   │   │   └── MyTicketsPage.tsx          # /meus-ingressos (UC07 — /api/ingressos/meus)
│   │   ├── organizador/                   # Telas sob /organizador
│   │   │   ├── DashboardPage.tsx          # /organizador — visão geral
│   │   │   ├── OrgEventoPage.tsx          # /organizador/evento — detalhe do evento ativo
│   │   │   ├── LotesPage.tsx              # /organizador/lotes (UC03)
│   │   │   ├── CheckinPage.tsx            # /organizador/checkin (UC04)
│   │   │   ├── CreateEventPage.tsx        # /organizador/eventos/novo (UC02)
│   │   │   ├── FinancePage.tsx            # /organizador/financeiro (preparado para UC14)
│   │   │   ├── AttendeesPage.tsx          # /organizador/participantes
│   │   │   └── shared.module.css          # Estilos compartilhados das telas /organizador
│   │   ├── LandingPage.tsx                # Página pública inicial (/)
│   │   └── LandingPage.module.css
│   ├── App.tsx                            # Definição de todas as rotas
│   ├── main.tsx                           # Entry point (ReactDOM + BrowserRouter)
│   └── index.css                          # Reset + variáveis CSS globais
├── index.html
├── vite.config.ts                         # host 0.0.0.0, porta 5173, strictPort (acesso via container)
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── eslint.config.js                       # ESLint flat config + react-hooks + react-refresh
├── Dockerfile                             # node:22-alpine, expõe 5173, CMD npm run dev
├── package.json
└── CLAUDE.md
```

---

## Variáveis de Ambiente

O frontend usa **uma única** variável (opcional), lida em build/dev pelo Vite:

```env
# URL base da API (default: http://localhost:8000/api)
VITE_API_URL=http://localhost:8000/api
```

Não há `.env` no diretório `frontend/` por padrão — o default cobre o fluxo local via Docker Compose. Em deploy, definir `VITE_API_URL` apontando para a URL pública do backend.

> Toda variável que precise chegar ao bundle do navegador **deve** começar com o prefixo `VITE_` (regra do Vite). Segredos nunca devem ser expostos no frontend.

---

## Como Rodar

O frontend roda exclusivamente via Docker Compose junto com o backend. O `Makefile` na raiz do repositório expõe os comandos principais.

```bash
# Sobe tudo (postgres + api + frontend). Frontend fica em http://localhost:5173
make up

# Logs do frontend em tempo real
docker compose logs -f frontend

# Instalar um pacote novo (mantém o lockfile dentro do container)
docker compose exec frontend npm install <pacote>

# Rodar lint
docker compose exec frontend npm run lint

# Build de produção (gera /dist)
docker compose exec frontend npm run build
```

Hot reload já está habilitado: o Compose monta `./frontend` como bind mount e o Vite recarrega ao salvar qualquer arquivo em `src/`.
