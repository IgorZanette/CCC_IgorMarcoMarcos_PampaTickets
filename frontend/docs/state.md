# state.md — Estado Atual do Desenvolvimento (Frontend)

> Atualizar este arquivo ao final de cada sessão de desenvolvimento.
> Objetivo: garantir continuidade entre sessões sem precisar reexplicar o contexto.

---

## Última atualização

**Data:** 26/05/2026
**Responsável:** Marco Antonio Santolin

> Mudanças recentes nesta sessão:
> 1. **Rotas flat** estilo Ticketmaster: `/app/*` deixou de existir (vira `/inicio`, `/eventos`, `/meus-ingressos`); `/org/*` virou `/organizador/*`. Pastas `src/pages/participant/` e `src/pages/organizer/` renomeadas para `participante/` e `organizador/`. Detalhes em [`requirements.md`](requirements.md#rotas).
> 2. **Remoção dos mocks** (`src/data/sample.ts` deletado). Todas as 13 pages e o `EventCard` consomem a API real. Novos clientes em `api/`: `lotes.ts`, `pedidos.ts`, `ingressos.ts`, `checkin.ts`. Novo helper `lib/active-event.ts` que persiste o id do evento ativo do organizador em localStorage. Campos sem suporte no backend (categoria/urgente/destaque/vendidos/precoMin/imagem) saíram da UI; imagem virou gradient determinístico por id. Dashboard, Financeiro e Participantes do organizador viraram placeholders explícitos enquanto UC14 e endpoints faltantes não chegam.

---

## O que foi implementado

### Infraestrutura

- [x] Projeto Vite + React 19 + TypeScript com ESLint (flat config) + `react-hooks` + `react-refresh`.
- [x] `Dockerfile` (node:22-alpine) e serviço `frontend` no `docker-compose.yml` raiz expondo `5173`.
- [x] `vite.config.ts` com `host: 0.0.0.0` + `strictPort: true` para o container ser acessível do host.
- [x] Estrutura de pastas em camadas: `api/`, `components/`, `data/`, `layouts/`, `lib/`, `pages/`.
- [x] CSS Modules como padrão de estilo, sem libs de UI externas.

### Auth (UC01)

- [x] Cliente axios em `api/client.ts` com interceptor que injeta JWT do `localStorage` (chave `pt_token`).
- [x] `api/auth.ts`: `login`, `cadastro`, `logout` + tipos `Usuario`, `Perfil`, `LoginPayload`, `CadastroPayload`.
- [x] Mini auth-store em `lib/auth-store.ts`: usuário em `localStorage` (`pt_user`) + hook `useCurrentUser()` que escuta `CustomEvent` (`pt-auth-change`) e `storage` (multi-aba). Sem Context.
- [x] Telas `LoginPage` e `CadastroPage` (sob `AuthShell`) com tratamento de erro via `extractErrorMessage`.
- [x] Pós-login redireciona para `/inicio` (participante) ou `/organizador` (organizador) baseado em `usuario.perfil`.

### Vitrine pública e participante (UC07 + UC12)

- [x] `api/eventos.ts`: `listarEventos`, `obterEvento`, `listarEventosOrganizador`, mutações de status (publicar/encerrar/cancelar), `gradientFor(id)` determinístico.
- [x] `api/lotes.ts`, `api/pedidos.ts`, `api/ingressos.ts`, `api/checkin.ts` — clientes tipados para todos os endpoints atualmente expostos pelo backend.
- [x] `HomePage` (`/inicio`), `SearchPage` (`/eventos`) e `EventoPage` (`/eventos/:id`) consumindo a vitrine real.
- [x] `EventoPage` puxa lotes via `GET /api/eventos/:id/lotes` e seleciona quantidades por `lote_id`.
- [x] `CheckoutPage` chama `POST /api/pedidos` (com método PIX/CREDIT_CARD/BOLETO); para PIX, renderiza o QR Code base64 (`pix_qrcode.encodedImage`) e o payload copiável.
- [x] `TicketsPage` lê `state` da rota (pedidoId + invoiceUrl), busca o pedido e tem botão "Atualizar status" para repuxar — sem polling automático.
- [x] `MyTicketsPage` consome `GET /api/ingressos/meus`, separa em "Próximos" (ATIVO + futuro) e "Histórico" (UTILIZADO/CANCELADO/passados); link de PDF quando `pdf_url` disponível.
- [x] `EventCard`, `DateBlock`, `StatusPill`, `ProgressBar`, `MetricCard`, `PageHeader`, `Logo` como componentes reutilizáveis.

### Organizador (UC02/UC03/UC04)

- [x] `lib/active-event.ts` — `useActiveEvent()` lê o id de evento ativo de `localStorage`; pages do organizador usam isso como seletor mínimo enquanto as rotas são singulares.
- [x] `DashboardPage` lista os eventos do organizador (`GET /api/organizador/eventos`) em cards; clicar define o evento ativo e navega para `OrgEventoPage`. Sem métricas — apresenta placeholder explícito para UC14.
- [x] `OrgEventoPage` exibe o evento ativo + ações de transição (Publicar / Encerrar / Cancelar) conforme `status`. Botões só aparecem se a transição for válida.
- [x] `LotesPage` consome `GET /api/organizador/eventos/:id/lotes` com Ativar/Desativar/Excluir. Botão "+ Criar lote" desabilitado por enquanto (formulário ainda não escrito).
- [x] `CreateEventPage` virou formulário único com os 5 campos do `EventoCreate` (nome, descrição, data_inicio, data_fim, local). Criação retorna o `Evento`, define-o como ativo e navega para `OrgEventoPage`.
- [x] `CheckinPage` chama `POST /api/checkin` com `qr_code_hash` colado manualmente; mantém um stream local dos últimos 20 ✓/✗ com mensagem de erro do backend.
- [x] `FinancePage` e `AttendeesPage` são placeholders explícitos — backend ainda não tem UC14 nem endpoint de listagem de ingressos por evento para o organizador.

### Utilitários

- [x] `lib/format.ts`: `money`, `moneyShort`, `dateShort`, `dateLong`, `dateFull`, `formatCpfCnpj`, `formatCelular`.
- [x] `lib/errors.ts`: `extractErrorMessage` entende `detail` como string OU lista de violações Pydantic, e remove o prefixo "Value error, " que o Pydantic adiciona em `@field_validator`.

---

## Em progresso

Nada em aberto. Próximo ciclo: criar lote no organizador (formulário em `LotesPage`), aplicar cupom no checkout (UC05) e botão de reembolso em `MyTicketsPage` (UC10).

---

## Próximo passo

1. **Criar lote no organizador**: `LotesPage` já lista/ativa/exclui via API; falta o formulário de **criar** (chama `POST /api/eventos/:id/lotes` — `criarLote` já existe em `api/lotes.ts`).
2. **Polling do pedido em PIX**: hoje `CheckoutPage` mostra o QR mas o usuário precisa entrar em `MyTicketsPage` pra ver se foi pago. Adicionar polling de `GET /api/pedidos/{id}` a cada ~5s enquanto status === PENDENTE.
3. **Cupons no checkout (UC05)**: input de código em `CheckoutPage`, preview via `POST /api/eventos/{id}/cupons/validar`, envio do `cupom_codigo` no `POST /api/pedidos`. Cliente `api/cupons.ts` ainda não existe.
4. **Reembolso (UC10)**: botão "Solicitar reembolso" em `MyTicketsPage` chamando `reembolsarPedido` (já existe em `api/pedidos.ts`).
5. **Leitor de QR de verdade** em `CheckinPage`: hoje aceita o hash colado manualmente. Adicionar `getUserMedia` + lib tipo `@zxing/browser`.
6. **Guards de rota**: `RequireAuth` em `/inicio`, `/meus-ingressos`, `/eventos/:id/checkout`, `/eventos/:id/ingressos`, `/organizador/*`. `RequirePerfil` para impedir participante em `/organizador` e vice-versa.

---

## Decisões tomadas até aqui

- **Sem libs de UI** (MUI/Chakra/etc.): identidade visual regional do projeto pede CSS próprio. CSS Modules por componente.
- **Sem Context para auth**: app é pequeno; `useCurrentUser` lê de `localStorage` e escuta `CustomEvent` + `storage`. Re-render só onde o hook é usado.
- **Sem fallback para mocks** (26/05/2026): a partir desta sessão, qualquer falha de API mostra mensagem de erro real ou estado vazio. `src/data/sample.ts` foi deletado, junto com toda a pasta `data/`. Decisão consciente: melhor refletir o estado real do backend (inclusive vazio) do que mascarar com dados fake que dão a impressão de funcionar.
- **Campos sem suporte saíram da UI** (26/05/2026): categoria, urgente, destaque, vendidos, precoMin, tags, imagem upload — todos eram inventados. Imagem virou `gradientFor(id)` (gradient determinístico por id). Categoria fica como follow-up se o backend ganhar o campo.
- **Seletor de evento ativo via localStorage** (26/05/2026): `lib/active-event.ts` persiste o id do "evento ativo do organizador" e `useActiveEvent()` hidrata o `Evento` completo. Atalho enquanto as rotas do organizador são singulares — some quando migrar para `/organizador/eventos/:id/...`.
- **Export nomeado** em todos os componentes (`export const Foo = ...`). Sem `export default`. Facilita renomeação e busca.
- **Cores e tokens** declarados em `:root` dentro de `src/index.css`. Referência via `var(--...)`. Não há ainda um arquivo separado de design tokens.
- **Tema por persona via layout** (`ParticipantLayout` escuro vs `OrganizerLayout` claro) em vez de toggle global. Decisão consciente: as personas têm contextos visuais distintos.
- **Rotas flat estilo Ticketmaster** (26/05/2026): saímos do padrão `/app/*` + `/org/*` e adotamos `/eventos`, `/eventos/:id`, `/meus-ingressos`, `/inicio` (sem prefixo) e `/organizador/*` para a área de gestão. `ParticipantLayout` envolve tanto a vitrine pública quanto as telas autenticadas — já lidava com o estado deslogado mostrando "Entrar". Pastas em `src/pages/` renomeadas de `participant`/`organizer` para `participante`/`organizador` (acentuação ok no filesystem). Rotas do organizador permanecem singulares por enquanto.
- **Erros do FastAPI tratados em um único lugar** (`lib/errors.ts`): aceita `detail` string ou lista de violações Pydantic, e remove o prefixo "Value error, " que aparece quando o backend usa `@field_validator`.
- **Hot reload via bind mount**: `docker-compose.yml` monta `./frontend` no container. Edições em `src/` recarregam sem rebuild. `node_modules` fica no volume da imagem para não conflitar com o host.

---

## Pendências conhecidas

- **Guards de rota ausentes**: hoje qualquer um navega para `/inicio`, `/meus-ingressos` ou `/organizador/*` sem auth. Backend rejeita as chamadas, mas a UX é ruim. Prioridade alta junto com o checkout.
- **Rotas singulares do organizador**: `/organizador/evento`, `/organizador/lotes`, `/organizador/checkin` assumem um evento ativo. Quando o front passar a suportar múltiplos eventos, migrar para `/organizador/eventos/:id/...` (lotes/participantes nested). O `OrganizerLayout` tem hard-coded "Festival de Inverno" no `EVENT_NAV` — sai junto com a refator.
- **Sem refresh token**: quando o JWT expira (60min), o usuário vê erros 401 silenciosos. Solução depende do backend implementar refresh primeiro.
- **Sem testes**: nenhum Vitest/Testing Library configurado. Dívida crítica antes do deploy.
- **Estados de loading/erro inconsistentes**: cada página trata do seu jeito. Falta um padrão (skeleton + retry).
- **Acessibilidade**: contraste do tema escuro, labels, foco visível em modais — nada revisado.
- **CORS em produção**: backend permite tudo hoje. Quando deploy, ajustar `VITE_API_URL` + lista de origens no backend.
- **Validação de força de senha no cadastro**: hoje só checa o que o backend devolver. Validar no front antes de enviar.
- **Polling vs WebSocket** para status do pagamento: a primeira versão do checkout vai usar polling (mais simples). Se virar gargalo, migrar para WS.
- **Backend sem categoria/imagem nos eventos**: chips de categoria foram removidos da UI. Imagens são gradients determinísticos por id. Se um dia o `Evento` ganhar `categoria` e `imagem_url`, repor.
- **`OrganizerLayout` ainda com "Festival de Inverno" hard-coded**: o `EVENT_NAV` mostra o título fixo. Quando `useActiveEvent()` for usado no layout, troca pelo nome real do evento ativo.
- **`AttendeesPage` e `FinancePage`** são placeholders enquanto não houver `GET /api/organizador/eventos/:id/ingressos` e UC14.
- **Cliente de cupons (`api/cupons.ts`)** ainda não existe — checkout não aplica desconto.
