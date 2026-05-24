# roadmap.md — Integrações e Prioridades de Implementação

## Ordem de implementação recomendada

Concluídos (em ordem cronológica):

1. ✅ Autenticação JWT (UC01)
2. ✅ Gerenciamento de Eventos e Lotes (UC02, UC03)
3. ✅ Fluxo de compra e pagamento via Asaas (UC07, UC09, UC11)
4. ✅ Geração de Ingresso PDF + Supabase Storage (UC12)
5. ✅ Check-in via QR Code (UC04)
6. ✅ Geração de Certificado PDF (UC13)
7. ✅ Reembolso (UC10)
8. ✅ Cupons (UC05)
9. ✅ Cortesias (UC06)

Pendentes:

10. Relatório Financeiro PDF (UC14)
11. Notificações WhatsApp (UC15)
12. Reembolso em massa por cancelamento de evento (extensão do UC10)
13. **Galeria de Fotos (UC08) — deixar por último**

---

## Integração: Asaas (Gateway de Pagamento)

Sandbox gratuito para testes: `https://sandbox.asaas.com/api/v3`
Documentação: https://docs.asaas.com

> **Onde fica o código:** toda chamada HTTP ao Asaas fica em [`app/integrations/asaas/`](../app/integrations/asaas/). A lógica de negócio (quando criar cobrança, orquestrar webhook → PDF → WhatsApp) fica em `service/pagamento_service.py` e `service/webhook_service.py`. Ver [requirements.md](requirements.md#camada-integrations--chamadas-a-apis-externas).

### Pré-requisito: cliente no Asaas

Toda cobrança no Asaas exige um `customer_id`. O fluxo é:

1. No primeiro pagamento do usuário, `pagamento_service` chama `integrations/asaas/customers.create_customer` com nome, email e CPF.
2. O `customer_id` retornado é persistido em `usuarios.asaas_customer_id`.
3. Nas próximas compras, reutilizar o `asaas_customer_id` — nunca recriar.

### Métodos de pagamento suportados
- Pix (preferencial)
- Boleto bancário
- Cartão de crédito

### Fluxo de pagamento

```
Participante finaliza compra
    → pagamento_service cria cobrança no Asaas
    → Asaas retorna link/QR Code de pagamento
    → Participante efetua o pagamento
    → Asaas dispara webhook para POST /webhooks/asaas
    → webhook_service processa o evento e atualiza status do pedido
    → Se confirmado → gera ingresso PDF → notifica via WhatsApp
    → Se expirado/cancelado → libera estoque do lote
```

### Eventos de webhook relevantes

| Evento | Ação no sistema |
|---|---|
| `PAYMENT_CONFIRMED` | Confirma pedido, cria ingressos com QR único, gera ingresso PDF, notifica participante |
| `PAYMENT_RECEIVED` | Mesmo fluxo (Pix instantâneo) |
| `PAYMENT_OVERDUE` | Cancela pedido, devolve estoque, deleta cobrança no Asaas |
| `PAYMENT_REFUNDED` | Marca pedido como reembolsado e pagamento como estornado |
| `PAYMENT_CREATED` | Ignorado (cobrança já registrada no fluxo síncrono); apenas log |

### Regras importantes
- O endpoint `POST /webhooks/asaas` é **público** (sem JWT), mas valida o token enviado pelo Asaas no header.
- Nunca liberar ingresso sem confirmação via webhook.
- Usar o `id` da cobrança do Asaas como chave externa na tabela `pagamentos`.

### Expondo o webhook em desenvolvimento local

O Asaas precisa de uma URL pública para disparar os webhooks. Use **ngrok**:

```bash
ngrok config add-authtoken SEU_TOKEN
ngrok http 8000
# URL gerada ex: https://abc123.ngrok-free.app
# Cadastrar no painel Asaas: https://abc123.ngrok-free.app/api/webhooks/asaas
```

> No plano gratuito do ngrok a URL muda a cada reinicialização — atualizar no painel do Asaas quando necessário.
> Alternativa gratuita com URL fixa: **Cloudflare Tunnel**.

---

## Integração: Supabase Storage (Armazenamento de PDFs)

Todos os PDFs gerados são armazenados no Supabase Storage — nunca no servidor local.

### Buckets

| Bucket | Conteúdo | UC |
|---|---|---|
| `ingressos` | PDFs de ingressos com QR Code | UC12 |
| `certificados` | PDFs de certificados | UC13 |
| `relatorios` | PDFs de relatórios financeiros | UC14 |

### Nomenclatura dos arquivos

```
ingressos/{ingresso_id}/ingresso_{ingresso_id}.pdf
certificados/{ingresso_id}/certificado_{ingresso_id}.pdf
relatorios/{evento_id}/{filename}.pdf
```

> A subestrutura por `evento_id`/`pedido_id` foi planejada mas não implementada. Hoje o caminho é apenas `<bucket>/<ingresso_id>/<filename>`. Se a granularidade for útil para o frontend (ex: agrupar arquivos por evento), refatorar `supabase_storage.py` num PR separado.

### Regras de acesso
- Ingressos e certificados: **URLs assinadas** com expiração (acesso temporário).
- Relatórios: **bucket privado** — apenas organizador autenticado acessa.
- URLs geradas são salvas nas respectivas tabelas no PostgreSQL.

---

## Integração: Meta Cloud API — WhatsApp Business

### Gatilhos de notificação

| Momento | Conteúdo da mensagem |
|---|---|
| Pagamento confirmado | Confirmação de compra + link do ingresso PDF |
| Check-in realizado | Link do certificado PDF |
| Véspera do evento | Lembrete com data, hora e local |
| Evento cancelado | Aviso + informações sobre reembolso |

### Regras importantes
- Envio sempre via `BackgroundTasks` — nunca bloqueia o fluxo principal.
- Usar apenas **templates aprovados** pela Meta para mensagens fora da janela de 24h.
- Somente o `whatsapp_service` acessa a API da Meta — nenhum outro service.
- Telefone do participante deve estar no formato: `+55DDNÚMERO`.