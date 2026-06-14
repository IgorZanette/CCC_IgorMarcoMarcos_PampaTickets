# state.md — Estado Atual do Desenvolvimento (Frontend)

> Atualizar este arquivo ao final de cada sessão de desenvolvimento.
> Objetivo: garantir continuidade entre sessões sem precisar reexplicar o contexto.

---

## Última atualização

**Data:** 14/06/2026
**Responsável:** Marco Antonio Santolin (dupla confirmação nas transições de evento + botão de certificado)

> **Dupla confirmação nas transições de evento (14/06/2026)** — `OrgEventoPage` em [src/pages/organizador/OrgEventoPage.tsx](../src/pages/organizador/OrgEventoPage.tsx) agora exibe `ConfirmDialog` antes de executar **Publicar**, **Encerrar** e **Cancelar evento**. Estado `confirm: null | "publicar" | "encerrar" | "cancelar"` controla qual diálogo está aberto. Os botões agora chamam `setConfirm(...)` em vez de `transicionar(...)` direto. "Cancelar evento" usa `danger={true}` (botão vermelho). Reusa o componente `ConfirmDialog` já existente em `src/components/`.
>
> **Botão "Baixar certificado" em Meus Ingressos (14/06/2026)** — `MyTicketsPage` em [src/pages/participante/MyTicketsPage.tsx](../src/pages/participante/MyTicketsPage.tsx) exibe botão "Baixar certificado" no card do ingresso quando `status === "UTILIZADO"` e `certificado_url` está disponível. Se UTILIZADO mas sem URL ainda, mostra "Certificado em geração…". Só aparece na aba **Histórico** (ingressos passados). Tipo `Ingresso` em [src/api/ingressos.ts](../src/api/ingressos.ts) ganhou campo `certificado_url: string | null`.

---

## Última atualização (anterior)

**Data:** 14/06/2026
**Responsável:** Marco Antonio Santolin (cartão + boleto UC09 + editar evento UC02)

> Cartão de crédito no checkout (14/06/2026 — branch `feat/pagamento-boleto`):
> 1. **Abordagem**: página segura hospedada do Asaas (redirecionamento) — o cartão nunca passa pelo servidor (fora do escopo PCI). Backend **inalterado** (já manda `billingType=CREDIT_CARD` e devolve `invoice_url`); o seletor e o hint já existiam.
> 2. **CTA de cartão na `PagamentoStatusPage`**: seção dedicada quando `metodo === "CREDIT_CARD"` com o botão de destaque **"💳 Pagar com cartão"** apontando para a `invoice_url`. A página passou a conhecer o `metodo` (do state da navegação + reidratado via `obterPagamento` no reload). O `CheckoutPage` repassa `metodo` no state.
> 3. **CTA compartilhado**: a classe `.boletoCta` virou `.payCta`, reusada por boleto e cartão. O botão genérico "Abrir fatura" agora só aparece como fallback (quando não há CTA dedicado).
>
> Destaque do botão de boleto (14/06/2026): "Abrir boleto" virou CTA primário em destaque (antes era link secundário discreto); linha digitável passou a alternativa "Ou copie a linha digitável".
>
> Boleto bancário no checkout (14/06/2026 — branch `feat/pagamento-boleto`):
> 1. **Seção de boleto na `PagamentoStatusPage`**: quando o pedido está aguardando e o método é boleto, mostra a **linha digitável** copiável (botão "Copiar linha digitável" via `navigator.clipboard`) + link "Abrir boleto (PDF)". Espelha a seção do PIX e reusa `.card`/`.hint`/`.pixPayload`/`.secondary`. Sobrevive a reload: reidrata o boleto via `obterPagamento` quando o state da navegação se perde (mesmo padrão do QR PIX).
> 2. **API**: novo tipo `Boleto` (`bankSlipUrl`, `identificationField`, `barCode`) e campo `boleto` em `PedidoCriado` e `PagamentoStatus` (`api/pedidos.ts`). O `CheckoutPage` repassa `criado.boleto` no state da navegação. O seletor de método e os hints já existiam.
> 3. **Backend**: vencimento de 3 dias para boleto + busca da linha digitável no Asaas (ver `backend/docs/state.md`).
>
> Editar evento (UC02) na `OrgEventoPage` (14/06/2026):
> 1. **Edição inline**: botão "Editar" no header abre um formulário no lugar do card de detalhes (nome, descrição, início, encerramento, local), pré-preenchido com os valores atuais. Salvar chama `PUT /eventos/:id` via `editarEvento`, atualiza o evento em memória (reflete na hora) e sai do modo edição. Erros do backend (409 status inválido, 422 data) aparecem via `extractErrorMessage`.
> 2. **Mesma regra do backend**: o botão "Editar" só aparece em **RASCUNHO** ou **PUBLICADO** (espelha `_STATUS_EDITAVEIS` do `evento_service`) — a UI nunca oferece uma edição que o servidor recusaria. Durante a edição, os botões de transição (Publicar/Encerrar/Cancelar) ficam ocultos para evitar ações conflitantes.
> 3. **Novo helper `utcIsoToLocalInput` em `lib/format.ts`**: inverso de `localToUtcIso` — converte o ISO UTC do backend para o valor `YYYY-MM-DDTHH:mm` do `<input type="datetime-local">` no fuso de São Paulo, para pré-preencher as datas. O formulário reusa o CSS do `CreateEventPage` para manter o visual idêntico.
>
> Reembolso do participante, primeira suíte de testes e CI (11/06/2026 — branch `feat/reembolso-participante`):
> 1. **Reembolso (UC10)**: botão "Solicitar reembolso" nos ingressos ATIVOS de eventos futuros em `MyTicketsPage` + `ReembolsoModal` (motivo opcional ≤500 chars, aviso de que o reembolso vale para o **pedido inteiro**, focus trap, Escape/overlay bloqueados durante o envio). `Ingresso` ganhou `pedido_id` (nulo p/ cortesia) e `reembolso_solicitado` vindos do backend — o estado "solicitado · aguardando confirmação" **sobrevive a reload** (o status real do ingresso só muda quando o webhook do Asaas confirmar o estorno).
> 2. **Suíte de testes (Vitest + Testing Library — 32 testes, `npm test`)**: `avaliarLote` (espelho das regras do backend), formatadores pt-BR/fuso SP, `extractErrorMessage`, guards do `RequireAuth` e o fluxo completo do reembolso (sucesso multi-ingresso, motivo null, estado do backend, cortesia sem botão, 409 mantém o modal). Setup em `src/test/setup.ts` (jsdom + jest-dom + cleanup explícito — globals desativados); `vite.config.ts` passou a importar de `vitest/config`.
> 3. **CI (GitHub Actions)**: `.github/workflows/ci.yml` roda ruff+pytest no backend e eslint+vitest+build aqui, em PRs e push na main.
> 4. **Renovação deslizante de sessão**: o interceptor de request (`api/client.ts`) renova o JWT via `POST /auth/refresh` quando faltam <20min para expirar (single-flight; falha cai no fluxo de 401). Helper `tokenExpMs` exportado e testado. Acaba o 401 silencioso aos 60min para quem está usando o app — o teto absoluto de 12h (backend) ainda exige novo login uma vez por dia.
> 5. **Recuperação de senha endurecida** (branch `fix/recuperacao-senha-hardening`): `ResetPasswordPage` passou a enviar o **token** devolvido pela validação em vez do código (o código de 6 dígitos não transita mais após validado — nem fica no history state do navegador); `ValidateCodePage` ganhou o link "Solicitar novo código" (saída para o lockout de 5 tentativas do backend); `ForgotPasswordPage` com copy genérica anti-enumeração ("Se o e-mail estiver cadastrado…") e os `setTimeout` de redirecionamento dos formulários agora têm cleanup via `useEffect` (sem navegação espúria se o usuário sair antes).
>
> Disponibilidade de lote no fluxo de compra (11/06/2026) — **helper compartilhado + revalidação no checkout**:
> 1. **Novo `lib/lote.ts` (`avaliarLote`)**: helper que espelha as regras de compra do backend (`pedido_service.criar`) — um lote só é comprável se estiver **ativo, dentro da janela de venda e com estoque**. Centraliza os motivos de indisponibilidade (`esgotado`, `encerrado`, `nao_iniciado`, `inativo`), seus rótulos e a precedência do rótulo (informação mais útil ao usuário primeiro). Retorna `{ disponivel, motivo, rotulo, restantes }`. As datas são comparadas como instantes (UTC), independente de fuso — a conversão de São Paulo é só para exibição.
> 2. **`EventoPage`**: deixou de calcular `esgotado`/`inativo` na mão e passou a usar `avaliarLote`. Os rótulos agora cobrem todos os motivos, incluindo **"Vendas abrem `<data>`"** para lotes ainda não iniciados (antes só mostrava "Esgotado"/"Indisponível"). `dateShort` adicionado ao import.
> 3. **`CheckoutPage`**: **revalida a disponibilidade antes de confirmar o pagamento** — um lote pode expirar ou esgotar entre a seleção e o checkout. Calcula `itensIndisponiveis` (sumido, indisponível, ou quantidade maior que a restante) e, se houver, **bloqueia o botão "Confirmar pagamento"** mostrando aviso amigável com o motivo por item + link "← Revisar ingressos", em vez de deixar o backend recusar com 409.
> 4. **Refactor id-aware (`active-event.ts` `useEvento` + métricas da `OrgEventoPage`)**: o resultado da API passou a carregar o `id` a que pertence (`{ id, evento/data, error }`). A staleness durante a navegação (resultado de um id anterior) virou **derivação no render** (`state?.id === id ? state : null`), eliminando o `setState` síncrono dentro do effect (lint `react-hooks/set-state-in-effect`) e os re-renders em cascata.
> 5. **UI**: marca da sidebar do organizador (`OrganizerLayout`) passou a empilhar logo + papel em coluna (`flex-direction: column`).
> 6. **Backend (chore)**: removida a config comentada do Meta WhatsApp (UC15) em `core/config.py` — será reintroduzida quando a integração for implementada.
>
> Reformulação do painel do organizador (30/05/2026) — **rotas por evento, fim do "evento ativo" em localStorage**:
> 1. **Rotas aninhadas por evento**: as telas do organizador passaram de rotas singulares (`/organizador/lotes`, `/cupons`, …) para `/organizador/eventos/:id/...` (`/lotes`, `/cupons`, `/cortesias`, `/checkin`, `/participantes`, `/financeiro`). O `:id` na URL é a fonte da verdade — dá pra abrir por link, o back do navegador e o refresh funcionam.
> 2. **Fim do localStorage de evento ativo**: `lib/active-event.ts` deixou de guardar/emitir o id em `localStorage`; virou o hook `useEvento(id)` que só hidrata o `Evento` a partir do id da rota. `getActiveEventId`/`setActiveEventId`/`useActiveEvent` removidos.
> 3. **OrganizerLayout**: lê o evento ativo da URL via `useMatch("/organizador/eventos/:id/*")`, hidrata uma vez e repassa via `Outlet context` (`type OrgOutlet = { evento, loading, error }`). A sidebar tem duas camadas: "Eventos" (lista) sempre; seção do evento (nome + `StatusPill` + "← Todos os eventos") só quando há `:id`. Removidos os itens cinza desabilitados (`TOP_NAV_DISABLED`) e a marca "P" hard-coded (agora usa `<Logo>` imagem, com `data-theme="dark"` no brand p/ contraste na sidebar escura).
> 4. **DashboardPage** virou só a **lista** de eventos; clicar abre `/organizador/eventos/:id`. As métricas/financeiro migraram para a **OrgEventoPage** (overview: métricas + status + descrição + transições + atalhos).
> 5. **Sub-páginas** trocaram `useActiveEvent()` por `useParams<{id}>()` (id p/ API) + `useOutletContext<OrgOutlet>()` (nome do evento no breadcrumb). Empty-states "Nenhum evento selecionado" removidos; id inválido cai em "Evento não encontrado".
> 6. **CreateEventPage** navega para `/organizador/eventos/${novo.id}` após criar.
>
> Ajustes de UI (30/05/2026) — **polimento de marca e limpeza de placeholders**:
> 1. **Logo por imagem**: `Logo.tsx` deixou de desenhar o quadradinho "P" via CSS e passou a usar a imagem real da marca (`public/logo.png`) como ícone, mantendo o wordmark "pampa*tickets*" ao lado (`size` controla a altura do `<img>`). Reflete em landing, auth (login/cadastro) e topo do participante. CSS: `.mark` virou `.img`; `.wordmark` mantido.
> 2. **Login limpo**: removido o texto de teste "Sem backend rodando? Use /inicio ou /organizador para ver o demo." da `LoginPage`.
> 3. **City chip removido**: o botão fixo "📍 Porto Alegre ▾" saiu do `ParticipantLayout` (e a regra `.cityChip` do CSS) — não tinha função.
> 4. **favicon.svg** atualizado para a nova marca.
>
> Mudanças anteriores nesta sessão (30/05/2026) — **painel do organizador fechou paridade com o backend**:
> 1. **Criar lote (UC03)**: formulário inline expansível em `LotesPage` (botão "+ Criar lote" deixou de ser placeholder). Usa `criarLote`.
> 2. **Cupons (UC05)**: novo `api/cupons.ts` + `CuponsPage` (criar/listar/ativar-desativar/excluir).
> 3. **Cortesias (UC06)**: novo `api/cortesias.ts` + `CortesiasPage` (emitir por e-mail/listar/cancelar; select de lotes).
> 4. **Participantes**: `AttendeesPage` deixou de ser placeholder — consome o novo `GET /api/organizador/eventos/:id/ingressos` (`listarIngressosDoEvento`) com busca client-side.
> 5. **UC14 Relatório Financeiro**: `FinancePage` baixa o PDF (`baixarRelatorio`) e o `DashboardPage` mostra métricas reais (`obterResumoRelatorio` → `MetricCard`: receita líquida/bruta, descontos/reembolsos, ingressos vendidos/check-ins, comparecimento). A mensagem "UC14 não implementado" saiu.
> 6. **Landing**: removido o aviso de "demo/dados de exemplo/mocks". Os botões "Sou participante"/"Sou organizador" agora vão para `/cadastro` passando o perfil via `state` (o `CadastroPage` pré-seleciona o perfil).
> 7. **OrganizerLayout**: "Cupons" e "Cortesias" saíram de `TOP_NAV_DISABLED` e entraram no `EVENT_NAV` (navegáveis). O label fixo "Festival de Inverno" virou o nome do evento ativo (`useActiveEvent`).
> 8. **CSS**: novo `pages/organizador/orgForms.module.css` compartilhado (form + tabela) por Cupons/Cortesias/Attendees.
>
> Mudanças da sessão anterior (26/05/2026):
> 1. **Rotas flat** estilo Ticketmaster: `/app/*` deixou de existir (vira `/inicio`, `/eventos`, `/meus-ingressos`); `/org/*` virou `/organizador/*`. Pastas `src/pages/participant/` e `src/pages/organizer/` renomeadas para `participante/` e `organizador/`. Detalhes em [`requirements.md`](requirements.md#rotas).
> 2. **Remoção dos mocks** (`src/data/sample.ts` deletado). Todas as pages e o `EventCard` consomem a API real. Clientes em `api/`: `lotes.ts`, `pedidos.ts`, `ingressos.ts`, `checkin.ts`. Helper `lib/active-event.ts` que persiste o id do evento ativo do organizador em localStorage.

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

### Organizador (UC02/UC03/UC04/UC05/UC06/UC14)

- [x] `lib/active-event.ts` — `useActiveEvent()` lê o id de evento ativo de `localStorage`; pages do organizador usam isso como seletor mínimo enquanto as rotas são singulares.
- [x] `DashboardPage` lista os eventos do organizador (`GET /api/organizador/eventos`) em cards; clicar define o evento ativo e navega para `OrgEventoPage`. **Métricas reais (UC14)**: ao ter evento ativo, busca `obterResumoRelatorio` e mostra `MetricCard`s (receita líquida/bruta, descontos/reembolsos, ingressos vendidos/check-ins, % de comparecimento) + botão "Baixar relatório PDF".
- [x] `OrgEventoPage` exibe o evento ativo + ações de transição (Publicar / Encerrar / Cancelar) conforme `status`. Botões só aparecem se a transição for válida. Tem atalho para "Relatório financeiro".
- [x] `LotesPage` consome `GET /api/organizador/eventos/:id/lotes` com Ativar/Desativar/Excluir + **criação inline** ("+ Criar lote" via `criarLote`).
- [x] `CuponsPage` (UC05) — `api/cupons.ts`: criar (form inline), listar, ativar/desativar (via `editarCupom({ativo})`), excluir. Mostra `%` ou `R$` conforme `tipo_desconto`.
- [x] `CortesiasPage` (UC06) — `api/cortesias.ts`: emitir cortesia (select de lote + e-mail do beneficiado + motivo), listar, cancelar. Erro claro quando o e-mail não é de usuário cadastrado.
- [x] `AttendeesPage` — consome `GET /api/organizador/eventos/:id/ingressos` (`listarIngressosDoEvento`): tabela com participante (nome/email), lote, status (`StatusPill`) e data; busca client-side por nome/email.
- [x] `CreateEventPage` virou formulário único com os 5 campos do `EventoCreate` (nome, descrição, data_inicio, data_fim, local). Criação retorna o `Evento`, define-o como ativo e navega para `OrgEventoPage`.
- [x] `CheckinPage` chama `POST /api/checkin` com `qr_code_hash` colado manualmente; mantém um stream local dos últimos 20 ✓/✗ com mensagem de erro do backend.
- [x] `FinancePage` (UC14) — baixa o relatório financeiro do evento ativo em PDF via `baixarRelatorio` (blob → download).

### Utilitários

- [x] `lib/format.ts`: `money`, `moneyShort`, `dateShort`, `dateLong`, `dateFull`, `formatCpfCnpj`, `formatCelular`.
- [x] `lib/errors.ts`: `extractErrorMessage` entende `detail` como string OU lista de violações Pydantic, e remove o prefixo "Value error, " que o Pydantic adiciona em `@field_validator`.
- [x] `lib/lote.ts`: `avaliarLote(lote, agora?)` → `{ disponivel, motivo, rotulo, restantes }`. Espelha as regras de compra do backend (`pedido_service.criar`); usado em `EventoPage` (rótulos de disponibilidade) e `CheckoutPage` (bloqueio antes do pagamento). Motivos: `esgotado`, `encerrado`, `nao_iniciado`, `inativo`.

---

## Em progresso

Nada em aberto. O painel do organizador agora cobre todos os endpoints do backend (eventos, lotes, cupons, cortesias, check-in, participantes, relatório financeiro). Foco do próximo ciclo volta ao **lado do participante**: cupom no checkout (UC05), reembolso (UC10) e polling do pagamento PIX.

---

## Próximo passo

1. **Cupom no checkout (UC05 — participante)**: input de código em `CheckoutPage`, preview via `POST /api/eventos/{id}/cupons/validar`, envio do `cupom_codigo` no `POST /api/pedidos`. Obs: o cliente `api/cupons.ts` já existe (criado para o painel do organizador) — falta a função de validar/preview e o uso no checkout.
2. **Reembolso (UC10)**: botão "Solicitar reembolso" em `MyTicketsPage` chamando `reembolsarPedido` (já existe em `api/pedidos.ts`).
3. **Polling do pedido em PIX**: hoje `CheckoutPage` mostra o QR mas o usuário precisa entrar em `MyTicketsPage` pra ver se foi pago. Adicionar polling de `GET /api/pedidos/{id}` a cada ~5s enquanto status === PENDENTE.
4. **Leitor de QR de verdade** em `CheckinPage`: hoje aceita o hash colado manualmente. Adicionar `getUserMedia` + lib tipo `@zxing/browser`.
5. ~~**Editar evento (UC02)**: `PUT /api/eventos/:id` em `OrgEventoPage`.~~ resolvido em 14/06/2026: edição inline na `OrgEventoPage` (só em RASCUNHO/PUBLICADO, espelhando `_STATUS_EDITAVEIS`).
6. **Guards de rota**: `RequireAuth` em `/inicio`, `/meus-ingressos`, `/eventos/:id/checkout`, `/eventos/:id/ingressos`, `/organizador/*`. `RequirePerfil` para impedir participante em `/organizador` e vice-versa.

---

## Decisões tomadas até aqui

- **Sem libs de UI** (MUI/Chakra/etc.): identidade visual regional do projeto pede CSS próprio. CSS Modules por componente.
- **Sem Context para auth**: app é pequeno; `useCurrentUser` lê de `localStorage` e escuta `CustomEvent` + `storage`. Re-render só onde o hook é usado.
- **Sem fallback para mocks** (26/05/2026): a partir desta sessão, qualquer falha de API mostra mensagem de erro real ou estado vazio. `src/data/sample.ts` foi deletado, junto com toda a pasta `data/`. Decisão consciente: melhor refletir o estado real do backend (inclusive vazio) do que mascarar com dados fake que dão a impressão de funcionar.
- **Campos sem suporte saíram da UI** (26/05/2026): categoria, urgente, destaque, vendidos, precoMin, tags, imagem upload — todos eram inventados. Imagem virou `gradientFor(id)` (gradient determinístico por id). Categoria fica como follow-up se o backend ganhar o campo.
- ~~**Seletor de evento ativo via localStorage** (26/05/2026)~~ **superado em 30/05/2026**: a fonte da verdade do evento do organizador passou a ser o `:id` na URL (`/organizador/eventos/:id/...`). `lib/active-event.ts` virou o hook `useEvento(id)` (sem `localStorage`); o `OrganizerLayout` hidrata via `useMatch` e repassa por `Outlet context`.
- **Export nomeado** em todos os componentes (`export const Foo = ...`). Sem `export default`. Facilita renomeação e busca.
- **Cores e tokens** declarados em `:root` dentro de `src/index.css`. Referência via `var(--...)`. Não há ainda um arquivo separado de design tokens.
- **Tema por persona via layout** (`ParticipantLayout` escuro vs `OrganizerLayout` claro) em vez de toggle global. Decisão consciente: as personas têm contextos visuais distintos.
- **Rotas flat estilo Ticketmaster** (26/05/2026): saímos do padrão `/app/*` + `/org/*` e adotamos `/eventos`, `/eventos/:id`, `/meus-ingressos`, `/inicio` (sem prefixo) e `/organizador/*` para a área de gestão. `ParticipantLayout` envolve tanto a vitrine pública quanto as telas autenticadas — já lidava com o estado deslogado mostrando "Entrar". Pastas em `src/pages/` renomeadas de `participant`/`organizer` para `participante`/`organizador` (acentuação ok no filesystem). Rotas do organizador permanecem singulares por enquanto.
- **Erros do FastAPI tratados em um único lugar** (`lib/errors.ts`): aceita `detail` string ou lista de violações Pydantic, e remove o prefixo "Value error, " que aparece quando o backend usa `@field_validator`.
- **Hot reload via bind mount**: `docker-compose.yml` monta `./frontend` no container. Edições em `src/` recarregam sem rebuild. `node_modules` fica no volume da imagem para não conflitar com o host.

---

## Pendências conhecidas

- ~~**Guards de rota ausentes**~~ resolvido em 04/06/2026 (merge `ad83d78`): `RequireAuth` protege `/meus-ingressos`, checkout e `/organizador/*` (com validação de perfil).
- ~~**Rotas singulares do organizador**~~ resolvido em 30/05/2026: migradas para `/organizador/eventos/:id/...` (nested). O id vem da URL (`useParams`/`useMatch`), hidratado uma vez no `OrganizerLayout` e repassado via `Outlet context`. `useActiveEvent`/`localStorage` removidos (hook `useEvento(id)` no lugar).
- ~~**Sem refresh token**~~ resolvido em 11/06/2026: o interceptor de request em `api/client.ts` renova o token via `POST /auth/refresh` (single-flight) quando faltam <20min para expirar; sessão tem teto absoluto de 12h no backend. Falha de renovação cai no fluxo de 401 já existente.
- ~~**Sem testes**~~ resolvido em 11/06/2026: Vitest + Testing Library (32 testes, `npm test`), rodando também no CI.
- **Estados de loading/erro inconsistentes**: cada página trata do seu jeito. Falta um padrão (skeleton + retry).
- **Acessibilidade**: contraste do tema escuro, labels, foco visível em modais — nada revisado.
- **CORS em produção**: backend permite tudo hoje. Quando deploy, ajustar `VITE_API_URL` + lista de origens no backend.
- **Validação de força de senha no cadastro**: hoje só checa o que o backend devolver. Validar no front antes de enviar.
- **Polling vs WebSocket** para status do pagamento: polling entregue na `PagamentoStatusPage` (3s até o pedido sair de PENDENTE). Se virar gargalo, migrar para WS.
- **Backend sem categoria/imagem nos eventos**: chips de categoria foram removidos da UI. Imagens são gradients determinísticos por id. Se um dia o `Evento` ganhar `categoria` e `imagem_url`, repor.
- ~~**`OrganizerLayout` com "Festival de Inverno" hard-coded**~~ resolvido em 30/05/2026: `EVENT_NAV` mostra `evento?.nome` via `useActiveEvent()` (fallback "Evento").
- ~~**`AttendeesPage` e `FinancePage` placeholders**~~ resolvidos em 30/05/2026: `AttendeesPage` consome `GET /api/organizador/eventos/:id/ingressos`; `FinancePage` baixa o PDF do UC14 e o `DashboardPage` mostra as métricas via `/relatorio/resumo`.
- ~~**Cliente de cupons (`api/cupons.ts`)**~~ criado em 30/05/2026 para o painel do organizador (criar/listar/editar/excluir). **Falta ainda** a função de validar/preview e o uso no checkout do participante (UC05).
- ~~**Cupom no checkout do participante**~~ verificado como entregue em 11/06/2026: `CheckoutPage` tem input + preview via `validarCupom` (revalida cupom vindo da tela do evento) e envia `cupom_codigo` no pedido.
- ~~**Reembolso (UC10) sem botão**~~ resolvido em 11/06/2026: botão + modal em `MyTicketsPage`; backend expõe `pedido_id`/`reembolso_solicitado` no `IngressoResponse`.
