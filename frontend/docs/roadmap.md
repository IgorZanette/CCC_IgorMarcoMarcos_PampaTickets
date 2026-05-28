# roadmap.md — Prioridades de Implementação (Frontend)

## Ordem de implementação recomendada

Concluídos (em ordem aproximada):

1. ✅ Estrutura base (Vite + React 19 + TypeScript + Router + axios)
2. ✅ Layouts por persona (participante escuro / organizador claro / auth)
3. ✅ Landing page e fluxo de auth (login + cadastro) — UC01
4. ✅ Vitrine pública de eventos (`HomePage`, `SearchPage`, `EventoPage`) consumindo a API real — UC07 (descoberta)
5. ✅ Cliente axios + interceptor de JWT + tradução de erros (FastAPI `detail`)
6. ✅ Clientes tipados em `api/`: `eventos`, `lotes`, `pedidos`, `ingressos`, `checkin`
7. ✅ Checkout (UC07 + UC09) — `POST /api/pedidos`, QR Code PIX, três métodos (PIX/CREDIT_CARD/BOLETO)
8. ✅ Meus ingressos (UC07 + UC12) — `GET /api/ingressos/meus`, link de PDF quando disponível
9. ✅ CRUD do organizador (UC02): listar eventos, criar (RASCUNHO), publicar/encerrar/cancelar
10. ✅ Lotes (UC03) — listar, ativar/desativar, excluir. Criar ainda pendente.
11. ✅ Check-in (UC04) — endpoint integrado com input de hash; leitor de câmera ainda pendente
12. ✅ Remoção total dos mocks (`src/data/sample.ts` deletado em 26/05/2026)

Pendentes (alta prioridade — fechar paridade com o backend já entregue):

13. **Criar lote** em `LotesPage` — formulário usando `criarLote` (`POST /api/eventos/:id/lotes`).
14. **Polling do status do pedido em PIX** — hoje `CheckoutPage` mostra o QR mas o usuário precisa ir manualmente em "Meus ingressos" pra ver se foi pago.
15. **Aplicação de cupom no checkout (UC05)** — `api/cupons.ts` + input + preview via `POST /api/eventos/{id}/cupons/validar`.
16. **Reembolso (UC10)** — botão "Solicitar reembolso" em `MyTicketsPage`. `reembolsarPedido` já existe em `api/pedidos.ts`.
17. **Cortesias (UC06)** — tela na área do organizador para emitir/listar/cancelar cortesias por evento.
18. **Leitor de QR de verdade** em `CheckinPage` (hoje aceita hash colado manualmente).
19. **Editar evento (UC02)** — `PUT /api/eventos/:id` em `OrgEventoPage`.

Pendentes (média/baixa prioridade — dependem de UCs ainda não implementados no backend):

20. **Relatório financeiro (UC14)** — `FinancePage` é placeholder explícito. Quando o endpoint existir, baixar PDF do bucket `relatorios/`.
21. **Lista de participantes do evento** — `AttendeesPage` é placeholder. Backend não expõe `GET /api/organizador/eventos/:id/ingressos`.
22. **Galeria de fotos (UC08)** — telas de listagem e compra de fotos. Fica por último, junto com o backend correspondente.

---

## Cross-cutting (sem ordem fixa — encaixar quando fizer sentido)

- **Guards de rota**: hoje as rotas autenticadas (`/inicio`, `/meus-ingressos`, `/eventos/:id/checkout`, `/eventos/:id/ingressos`, `/organizador/*`) não validam auth no front. Adicionar `RequireAuth` (e talvez `RequirePerfil`) lendo de `useCurrentUser` e redirecionando para `/login`.
- **Refresh automático de token**: ainda não há. Quando o backend implementar refresh token, o interceptor de response no axios deve tratar 401 → renovar → retentar.
- **Estado de loading/erro padronizado**: várias páginas hoje renderizam mock direto. Definir um padrão (skeleton + estado de erro com retry) e aplicar em todas as telas que dependem da API.
- **Acessibilidade**: revisar contraste do tema escuro, labels de inputs, foco visível em modais. Nada estruturado hoje.
- **Testes**: ausência total de suíte. Quando entrar, começar por Vitest + Testing Library nos fluxos críticos (login, checkout, check-in).

---

## Backend que o frontend consome

Endpoints já implementados no backend (resumo — fonte de verdade em [`backend/docs/state.md`](../../backend/docs/state.md)):

| UC | Endpoint(s) | Status no front |
|---|---|---|
| UC01 | `POST /api/auth/cadastro`, `POST /api/auth/login`, `GET /api/auth/me` | ✅ Login e cadastro funcionando |
| UC02 | `POST/GET/PUT/DELETE /api/eventos` + `PATCH /publicar|encerrar|cancelar` | ✅ Listar/criar/publicar/encerrar/cancelar (editar pendente) |
| UC03 | CRUD de lotes em `/api/eventos/{id}/lotes` e `/api/lotes/{id}` | ✅ Listar/ativar/desativar/excluir (criar pendente) |
| UC04 | `POST /api/checkin` (body `{qr_code_hash}`, OrganizadorUser) | 🚧 Integrado, falta leitor de câmera |
| UC05 | Cupons (CRUD + `POST /api/eventos/{id}/cupons/validar`) | ❌ Não integrado |
| UC06 | Cortesias (emitir/listar/cancelar) | ❌ Sem tela |
| UC07 | `POST /api/pedidos`, `GET /api/pedidos/meus`, `GET /api/ingressos/meus` | ✅ Fluxo de compra ponta a ponta |
| UC09 | Integração Asaas (transparente — `POST /api/pedidos` já cria a cobrança e devolve `pix_qrcode`) | ✅ Checkout exibe QR PIX |
| UC10 | `POST /api/pedidos/{id}/reembolso` | 🚧 Cliente pronto, falta botão |
| UC11 | Webhook Asaas (back-end-only, sem UI) | — |
| UC12 | URL do PDF do ingresso vem em `ingresso.pdf_url` | ✅ `MyTicketsPage` linka o PDF |
| UC13 | URL do PDF do certificado vem em `certificado.pdf_url` | ❌ Sem endpoint de listagem ainda — discutir com o back |
| UC14 | Relatório financeiro PDF | ❌ Backend pendente (placeholder em `FinancePage`) |
| UC15 | WhatsApp (notificações server-side, sem UI) | — |
| UC08 | Galeria de fotos | ❌ Backend pendente |

---

## Decisões pendentes (precisa alinhar com o time)

1. **Onde mostrar o status do pagamento** depois do checkout: dentro da própria `TicketsPage` (polling) ou redirecionar para `MyTicketsPage`?
2. **Captura de QR no check-in**: usar `getUserMedia` + leitor JS (ex: `@zxing/browser`) ou aceitar input manual do hash como fallback obrigatório?
3. **Multi-evento no organizador**: `OrgEventoPage` hoje é singular (rotas `/organizador/evento`, `/organizador/lotes`, etc.). Precisamos de uma rota de seleção (`/organizador/eventos`) antes de entrar em um evento específico, e refatorar para `/organizador/eventos/:id/lotes`, `/organizador/eventos/:id/participantes` etc.?
4. **Tema**: as variáveis CSS estão hard-coded em `index.css`. Vale extrair tokens (cores, espaçamentos) para um arquivo de design system separado?
