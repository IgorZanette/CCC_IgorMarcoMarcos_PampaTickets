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
10. ✅ Relatório Financeiro (UC14) — PDF (`StreamingResponse`, sem Supabase) + resumo JSON para o dashboard
11. ✅ Listagem de ingressos por evento para o organizador (`GET /api/organizador/eventos/{id}/ingressos`)

Pendentes:

12. Notificações WhatsApp (UC15)
13. Reembolso em massa por cancelamento de evento (extensão do UC10)
14. **Galeria de Fotos (UC08) — deixar por último**

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
| `relatorios` | ~~PDFs de relatórios financeiros~~ — **não usado**. UC14 serve o PDF direto pela API (ver abaixo) | UC14 |

### Nomenclatura dos arquivos

```
ingressos/{ingresso_id}/ingresso_{ingresso_id}.pdf
certificados/{ingresso_id}/certificado_{ingresso_id}.pdf
relatorios/{evento_id}/{filename}.pdf
```

> A subestrutura por `evento_id`/`pedido_id` foi planejada mas não implementada. Hoje o caminho é apenas `<bucket>/<ingresso_id>/<filename>`. Se a granularidade for útil para o frontend (ex: agrupar arquivos por evento), refatorar `supabase_storage.py` num PR separado.

### Regras de acesso
- Ingressos e certificados: **URLs assinadas** com expiração (acesso temporário).
- Relatórios (UC14): **não passam pelo Supabase**. O PDF é gerado sob demanda e servido direto pela API via `StreamingResponse`, protegido por `OrganizadorUser` (ver `app/api/routes/relatorios.py`). Decisão de 30/05/2026: relatório é sensível e sempre fresco — servir pela API evita bucket privado + signed URLs que expiram/vazam.
- URLs geradas (ingressos/certificados) são salvas nas respectivas tabelas no PostgreSQL.

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

---

## UC08 — Galeria de Fotos (plano, ainda não implementado)

> Último UC pendente (baixa prioridade). Plano acordado para não se perder — **ainda não implementado**.

### Decisões da v1 (MVP)
- **Galeria grátis**: o organizador publica as fotos do evento; participantes/visitantes do evento
  publicado veem e baixam livremente. **Sem compra** nesta versão — `preco` e o model `CompraFoto`
  ficam sem uso por ora (como o model `Relatorio` no UC14), reservados para uma fase paga futura.
- **Upload pelo organizador**, reusando a posse do evento (igual lotes/cupons/cortesias). **Sem perfil
  FOTOGRAFO** — o model `FotoEvento` só tem `evento_id`, então nada de enum novo nem migration.
- **Sem processamento de imagem** (sem Pillow): sobe a imagem como veio; `url_thumbnail` e
  `url_original` recebem a **mesma URL pública** (preview escalado via CSS no front).
- **Sem migration**: as tabelas `fotos_evento`/`compras_foto` já existem; campos NOT NULL preenchidos
  (`preco = 0` na galeria grátis).

### Backend (espelha o padrão repo→service→route de cupons/cortesias)
- **Config** (`core/config.py`): `SUPABASE_BUCKET_FOTOS = "fotos"`, `MAX_FOTO_SIZE_MB = 10`,
  `ALLOWED_FOTO_TYPES = ["image/jpeg", "image/png", "image/webp"]`.
- **Dependência**: `uv add python-multipart` (FastAPI precisa dela para `UploadFile`; não está no
  projeto pois não há upload hoje).
- **Storage** (`integrations/supabase/supabase_storage.py`): `upload_foto_evento(file, filename,
  evento_id) -> str` (bucket de fotos, path `{evento_id}/{uuid}.{ext}`, URL pública via
  `get_public_url`) + `remover_foto(path)` best-effort. Reusa o helper `_to_bytes`.
- **Novos**: `repositories/foto_repo.py` (CRUD), `service/foto_service.py` (`publicar` valida
  posse/tipo/tamanho e sobe; `listar_por_evento`; `excluir` valida posse + remove do storage),
  `schemas/foto.py` (`FotoResponse`), `api/routes/fotos.py` registrado em `main.py`.
- **Rotas**: `POST /api/eventos/{evento_id}/fotos` (`OrganizadorUser`, `UploadFile`, 201);
  `GET /api/eventos/{evento_id}/fotos` (público); `DELETE /api/fotos/{foto_id}` (dono, 204).

### Frontend
- `api/fotos.ts` (`listarFotos`, `enviarFoto` via multipart, `excluirFoto`).
- Organizador: página `OrgFotosPage` em `/organizador/eventos/:id/fotos` (entra no `EVENT_NAV`) —
  input de arquivo + grid com excluir.
- Participante: seção "Galeria" na `EventoPage` (grid + link para baixar o original).

### Evolução futura (fora da v1)
- **Galeria paga**: ativar `preco` + `CompraFoto` reusando o `Pedido`/Asaas; original em bucket
  **privado** + **URL assinada** só para quem comprou; o webhook (que hoje cria ingressos) passaria a
  também liberar as `CompraFoto` do pedido. Preview com marca d'água (Pillow).
- **Perfil FOTOGRAFO**: enum + migration + FK/vínculo evento↔fotógrafo + deps de auth, caso vire um
  marketplace de fotógrafos independentes.