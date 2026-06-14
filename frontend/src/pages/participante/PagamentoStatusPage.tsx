import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { obterEvento, type Evento } from "../../api/eventos";
import {
  obterPagamento,
  obterPedido,
  type Boleto,
  type Pedido,
  type PixQrCode,
} from "../../api/pedidos";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, money } from "../../lib/format";

import styles from "./PagamentoStatusPage.module.css";

type LocationState = {
  invoiceUrl?: string;
  pixQrcode?: PixQrCode | null;
  boleto?: Boleto | null;
} | null;

// Intervalo do polling. A API atualiza o status do pedido quando o webhook do
// Asaas chega; aqui consultamos periodicamente até sair de PENDENTE.
const POLL_MS = 3000;

export const PagamentoStatusPage = () => {
  const { id, pedidoId } = useParams();
  const location = useLocation();
  const state = location.state as LocationState;
  const [invoiceUrl, setInvoiceUrl] = useState<string | undefined>(
    state?.invoiceUrl,
  );
  const [pixQrcode, setPixQrcode] = useState<PixQrCode | null>(
    state?.pixQrcode ?? null,
  );
  const [boleto, setBoleto] = useState<Boleto | null>(state?.boleto ?? null);
  const [copiado, setCopiado] = useState(false);

  const [ev, setEv] = useState<Evento | null>(null);
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    obterEvento(id).then(setEv).catch(() => undefined);
  }, [id]);

  // #10: reidrata fatura/QR PIX/boleto quando o state da navegação se perdeu
  // (refresh, link direto ou voltar/avançar) — sem isso o usuário ficaria sem
  // como pagar.
  useEffect(() => {
    if (!pedidoId) return;
    if (state?.invoiceUrl || state?.pixQrcode || state?.boleto) return;
    let cancelled = false;
    obterPagamento(pedidoId)
      .then((p) => {
        if (cancelled) return;
        setInvoiceUrl(p.invoice_url ?? undefined);
        setPixQrcode(p.pix_qrcode);
        setBoleto(p.boleto);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [pedidoId, state]);

  useEffect(() => {
    if (!pedidoId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const p = await obterPedido(pedidoId);
        if (cancelled) return;
        setPedido(p);
        // Continua perguntando enquanto o pagamento não foi resolvido.
        if (p.status === "PENDENTE") timer = setTimeout(tick, POLL_MS);
      } catch (err) {
        if (cancelled) return;
        setError(extractErrorMessage(err, "Falha ao consultar o pagamento."));
        timer = setTimeout(tick, POLL_MS);
      }
    };
    tick();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [pedidoId]);

  const status = pedido?.status;
  const pago = status === "PAGO";
  const falhou = status === "CANCELADO" || status === "REEMBOLSADO";
  const aguardando = !falhou && !pago;

  const icone = pago ? "✓" : falhou ? "✕" : "⏳";
  const titulo = pago
    ? "Compra realizada com sucesso!"
    : falhou
      ? "Pagamento não confirmado"
      : "Aguardando pagamento";
  const subtitulo = pago
    ? "Seus ingressos foram emitidos e já estão disponíveis em Meus ingressos."
    : falhou
      ? "Não conseguimos confirmar o pagamento deste pedido. Nenhum valor foi cobrado e os ingressos não foram emitidos."
      : "Assim que o pagamento for confirmado, esta tela é atualizada automaticamente.";

  const copiarLinhaDigitavel = async () => {
    if (!boleto?.identificationField) return;
    try {
      await navigator.clipboard.writeText(boleto.identificationField);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // Sem clipboard (contexto não-seguro): o campo segue selecionável manualmente.
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div
          className={styles.icon}
          data-state={pago ? "ok" : falhou ? "fail" : "wait"}
        >
          {icone}
        </div>
        <h1 className={styles.title}>{titulo}</h1>
        <p className={styles.lead}>{subtitulo}</p>
        {aguardando && <div className={styles.spinner} aria-hidden />}
      </header>

      {aguardando && pixQrcode && (
        <section className={styles.card}>
          <h3 className={styles.cardTitle}>Pague com PIX</h3>
          <div className={styles.pixWrap}>
            <img
              src={`data:image/png;base64,${pixQrcode.encodedImage}`}
              alt="QR Code PIX"
              className={styles.pixQr}
            />
            <div>
              <div className={styles.hint}>
                Escaneie o QR Code com o app do seu banco ou copie o código abaixo.
              </div>
              <textarea
                readOnly
                value={pixQrcode.payload}
                className={styles.pixPayload}
              />
            </div>
          </div>
        </section>
      )}

      {aguardando && boleto && (
        <section className={styles.card}>
          <h3 className={styles.cardTitle}>Pague com boleto</h3>
          <div className={styles.boletoWrap}>
            <div className={styles.hint}>
              Copie a linha digitável e pague no app ou site do seu banco. A
              compensação leva até 3 dias úteis — seus ingressos são emitidos
              assim que o pagamento for confirmado.
            </div>
            {boleto.identificationField && (
              <>
                <textarea
                  readOnly
                  value={boleto.identificationField}
                  className={styles.pixPayload}
                />
                <button
                  type="button"
                  className={styles.secondary}
                  onClick={copiarLinhaDigitavel}
                >
                  {copiado ? "Copiado ✓" : "Copiar linha digitável"}
                </button>
              </>
            )}
            {boleto.bankSlipUrl && (
              <a
                href={boleto.bankSlipUrl}
                target="_blank"
                rel="noreferrer"
                className={styles.secondary}
              >
                Abrir boleto (PDF)
              </a>
            )}
          </div>
        </section>
      )}

      {(ev || pedido) && (
        <section className={styles.card}>
          <div className={styles.details}>
            {ev && (
              <>
                <Detail label="Evento" value={ev.nome} />
                <Detail label="Data" value={dateLong(ev.data_inicio)} />
              </>
            )}
            {pedido && (
              <>
                <Detail label="Pedido" value={`#${pedido.id.slice(0, 8)}`} />
                <Detail label="Total" value={money(pedido.valor_total)} />
                <Detail label="Status" value={pedido.status} />
              </>
            )}
          </div>
        </section>
      )}

      {error && <div className={styles.errorMsg}>⚠ {error}</div>}

      <div className={styles.actions}>
        {aguardando && invoiceUrl && (
          <a
            href={invoiceUrl}
            target="_blank"
            rel="noreferrer"
            className={styles.secondary}
          >
            Abrir fatura
          </a>
        )}
        {falhou && id && (
          <Link to={`/eventos/${id}`} className={styles.secondary}>
            Voltar ao evento
          </Link>
        )}
        {pago && (
          <Link to="/meus-ingressos" className={styles.primary}>
            Meus ingressos
          </Link>
        )}
        {!pago && (
          <Link to="/eventos" className={falhou ? styles.primary : styles.secondary}>
            Explorar eventos
          </Link>
        )}
      </div>
    </div>
  );
};

const Detail = ({ label, value }: { label: string; value: string }) => (
  <div>
    <div className={styles.detailLabel}>{label}</div>
    <div className={styles.detailValue}>{value}</div>
  </div>
);
