# CLAUDE.md — pampatickets (Frontend)

Arquivo de índice. Não contém regras detalhadas — aponta para os documentos especializados em `docs/`.
Leia apenas o arquivo relevante para a tarefa em execução.

---

## Documentos de referência

| Arquivo | Quando ler |
|---|---|
| [`docs/project.md`](docs/project.md) | Visão geral, stack técnica e estrutura de pastas |
| [`docs/requirements.md`](docs/requirements.md) | Regras de arquitetura, padrões de UI e convenções |
| [`docs/roadmap.md`](docs/roadmap.md) | Prioridades de implementação e telas pendentes |
| [`docs/state.md`](docs/state.md) | Estado atual do desenvolvimento — atualizar a cada sessão |

---

## Regras globais (sempre aplicar)

- Gerenciamento de pacotes: **sempre `npm install`** dentro do container (`docker compose exec frontend npm install <pacote>`), nunca editar `package.json` à mão
- Comentários e textos voltados ao usuário: **português**
- Nomenclatura técnica (variáveis, funções, componentes): **inglês** (ex: `EventCard`, `useCurrentUser`)
- Estilos: **CSS Modules** (`*.module.css`) por componente/página — sem CSS global fora de `index.css`
- Commits: português, padrão `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Toda chamada HTTP passa pelo cliente axios em [`src/api/client.ts`](src/api/client.ts) — JWT é injetado automaticamente
