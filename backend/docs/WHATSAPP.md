# Notificações WhatsApp (UC15)

Notificações transacionais via **Meta Cloud API** (WhatsApp Business). Entregue
como **draft estrutural**: a integração está completa, testada (Meta mockada) e
liga nos gatilhos reais, mas o envio efetivo depende de credenciais e templates
aprovados que ainda não temos — sem eles, tudo degrada para **no-op gracioso**.

## Arquitetura

Segue o padrão das demais integrações (Asaas/Supabase): HTTP isolado na camada
`integrations/`, orquestração no `service/`, degradação graciosa.

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Integração | [`app/integrations/whatsapp/client.py`](../app/integrations/whatsapp/client.py) | **Único** ponto que fala com a Meta. `send_template_message` faz no-op sem credenciais. |
| Integração | [`app/integrations/whatsapp/exceptions.py`](../app/integrations/whatsapp/exceptions.py) | `WhatsAppAPIError` (status + corpo), espelha `AsaasAPIError`. |
| Serviço | [`app/service/whatsapp_service.py`](../app/service/whatsapp_service.py) | Único orquestrador: normaliza telefone, monta template, agenda envio, trata erro. |
| Helper | [`app/core/phone.py`](../app/core/phone.py) | `to_e164_br` → `+55DDNÚMERO`. |

## Gatilhos (event-driven, sempre via `BackgroundTasks`)

| Gatilho | Onde dispara | Template |
|---|---|---|
| Pagamento confirmado | `pagamento_service.processar_webhook` (só na transição efetiva para PAGO) | `pagamento_confirmado` |
| Check-in realizado | `ingresso_service.validar_checkin` (após gerar certificado) | `checkin_realizado` |
| Evento cancelado | `cancelamento_service.cancelar_pedidos_do_evento` (um por participante) | `evento_cancelado` |

> **Fora deste escopo (follow-up):** o gatilho "véspera do evento" precisa de um
> scheduler (cron/job agendado) que o projeto ainda não tem — é um subsistema à
> parte.

## Garantias de design

- **Best-effort**: falha de envio é logada, nunca propaga para o fluxo principal
  (pagamento, check-in, cancelamento). Sem credenciais, nada é enviado.
- **Idempotência**: o gatilho de pagamento dispara só na transição efetiva —
  reentregas do webhook (bloco idempotente que reemite ingressos) não
  renotificam.
- **Telefone inválido** (não normalizável para E.164) → não envia, loga.
- **PII**: o telefone nunca aparece em log; o `request_id` do middleware
  correlaciona.

## Configuração

```bash
META_WHATSAPP_TOKEN=...      # access token da Meta Cloud API
META_PHONE_NUMBER_ID=...     # id do número remetente
META_API_VERSION=v21.0       # opcional (default v21.0)
FRONTEND_URL=https://...     # base usada para links nas notificações
```

## Pendente para produção (supervisão humana)

1. **Credenciais reais** da Meta Cloud API + número WhatsApp Business verificado.
2. **Templates aprovados** no Meta Business Manager com os nomes em
   `whatsapp_service` (`pagamento_confirmado`, `checkin_realizado`,
   `evento_cancelado`), cada um com placeholders de corpo `{{1}}` (nome) e
   `{{2}}` (evento). Mensagens iniciadas pelo negócio (fora da janela de 24h)
   **exigem** template aprovado.
3. **Teste E2E real** com um número de teste, como feito com o sandbox do Asaas.
4. Gatilho **véspera do evento** (scheduler).
