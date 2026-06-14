# requirements.md — Regras de Arquitetura e Domínio

Documento de referência para decisões arquiteturais. Toda contribuição ao backend deve seguir estas regras.

---

## Camadas da aplicação

| Camada | Responsabilidade | Nunca pode |
|---|---|---|
| `api/routes/` | Recebe requisição, valida via schema, delega para `service/`, retorna resposta. | Conter lógica de negócio, acessar `repositories/` ou `integrations/` diretamente. |
| `schemas/` | DTOs Pydantic de entrada e saída da API. | Conter lógica ou importar `models/`. |
| `service/` | **Toda** a lógica de negócio e orquestração de fluxos. | Importar `httpx` ou usar `AsyncSession` diretamente — sempre via `repositories/` ou `integrations/`. |
| `repositories/` | Acesso ao banco de dados (CRUD, queries). | Conter regra de negócio. |
| `models/` | Entidades ORM (SQLAlchemy). | Ser retornadas direto pela API. |
| `integrations/` | Clientes HTTP para APIs externas (Asaas, Supabase, Meta). | Conter regra de negócio, importar de `service/`, `repositories/` ou `models/`. |
| `reports/` | Geração assíncrona de PDF via ReportLab. | Fazer upload (isso é responsabilidade de `integrations/supabase`). |

**Dependência unidirecional:** `routes → service → {repositories, integrations, reports}`. Nunca o inverso.

---

## Camada `integrations/` — chamadas a APIs externas

### Por que existe

Separar a **tradução de protocolo** (formato de request/response da API externa) da **lógica de negócio** (quando e por quê chamar). Isso facilita testes (mockar `integrations/` ao testar `service/`) e evita acoplamento ao formato do provedor.

### Regras

1. **Um subpacote por provedor**: `integrations/asaas/`, `integrations/supabase/`, `integrations/whatsapp/`.
2. **Apenas `integrations/` importa `httpx`.** Se um service precisar, é sinal de que falta função em `integrations/`.
3. **Cliente HTTP é singleton** do módulo (`httpx.AsyncClient`), instanciado uma vez e fechado no `lifespan` do FastAPI.
4. **Funções tipadas com schemas próprios.** Cada integração tem seu `schemas.py` (Pydantic) — não reutilizar os de `app/schemas/`, que são contrato da nossa API.
5. **Exceções próprias** (ex: `AsaasAPIError`). O `service/` captura e traduz para `HTTPException`. `integrations/` nunca levanta `HTTPException` do FastAPI.
6. **Nenhum acesso a banco ou model** dentro de `integrations/`.
7. **Configuração via `app/core/config.settings`** — nunca ler `os.environ` diretamente.

### Exemplo de uso

```python
# service/pagamento_service.py
from app.integrations.asaas import customers as asaas_customers
from app.integrations.asaas import payments as asaas_payments
from app.integrations.asaas.exceptions import AsaasAPIError

async def criar_cobranca_pedido(db, usuario, pedido):
    if not usuario.asaas_customer_id:
        try:
            customer = await asaas_customers.create_customer(
                nome=usuario.nome, email=usuario.email, cpf=usuario.cpf
            )
        except AsaasAPIError:
            raise HTTPException(502, "Falha ao registrar cliente no gateway.")
        await usuario_repo.set_asaas_id(db, usuario.id, customer.id)

    cobranca = await asaas_payments.create_payment(
        customer_id=usuario.asaas_customer_id, valor=pedido.total, ...
    )
    await pagamento_repo.create(db, pedido_id=pedido.id, asaas_id=cobranca.id)
    return cobranca
```

---

## Regras gerais de código

1. **Routers não contêm lógica de negócio** — recebem, delegam, devolvem.
2. **Nunca retornar entidade SQLAlchemy direto** — sempre via schema Pydantic.
3. **Validar todo input via Pydantic** antes da camada de serviço.
4. **Geração de PDF é sempre assíncrona** (`BackgroundTasks` ou `asyncio.create_task`) — nunca bloquear a API.
5. **Endpoints públicos**: apenas cadastro, login, listagem pública de eventos e webhooks do Asaas. Qualquer outro precisa de justificativa.
6. **Repositórios são os únicos com acesso ao banco** — services nunca usam `AsyncSession` direto.
7. **Pagamento só é considerado confirmado via webhook** (`PAYMENT_CONFIRMED`/`PAYMENT_RECEIVED`). Nunca confiar na resposta de criação da cobrança.

---

## Convenções de código

- **Idioma:** comentários, nomes de domínio e mensagens de erro ao usuário em **português**. Nomenclatura técnica em **inglês** (`get_by_id`, `create_evento`).
- **Imports** ordenados alfabeticamente dentro de cada grupo.
- **Commits** em português: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- **Pacotes:** sempre `uv add` / `uv remove`. Nunca `pip install`.

---

## Domínio do negócio

| Entidade | Descrição |
|---|---|
| Usuário | Organizador ou participante |
| Evento | Show, festival, teatro, etc. |
| Lote | Agrupamento de ingressos com tipo, preço e quantidade |
| Ingresso | Unidade adquirida por um usuário |
| Pedido | Agrupamento de ingressos de uma compra |
| Pagamento | Transação financeira associada a um pedido |
| Cupom | Desconto aplicável na compra |
| Cortesia | Ingresso gratuito emitido pelo organizador |
| Check-in | Validação de entrada via QR Code |
| Certificado | PDF emitido após check-in |
| Foto | Imagem do evento na galeria |
| Relatório | PDF financeiro |

---

## Casos de uso

| UC | Descrição | Prioridade |
|---|---|---|
| UC01 | Autenticar (login, cadastro, recuperação) | Alta |
| UC02 | Gerenciar Evento | Alta |
| UC03 | Gerenciar Ingressos (lotes, tipos, preços) | Alta |
| UC04 | Check-in via QR Code | Alta |
| UC05 | Cupons de desconto | Alta |
| UC06 | Cortesias | Alta |
| UC07 | Buscar e Comprar Ingressos | Alta |
| UC09 | Processar Pagamento via Asaas | Alta |
| UC10 | Reembolso via Asaas | Alta |
| UC11 | Receber Webhooks do Asaas | Alta |
| UC12 | Gerar Ingresso PDF com QR Code | Alta |
| UC13 | Gerar Certificado PDF | Alta |
| UC14 | Gerar Relatório Financeiro PDF | Média |
| UC15 | Notificar via WhatsApp | Média |
| UC08 | Galeria de Fotos | Baixa — implementado (v1 grátis; visualização exige login) |