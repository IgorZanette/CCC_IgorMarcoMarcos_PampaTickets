import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { obterEvento, type Evento } from "../../api/eventos";
import { listarLotes, type Lote } from "../../api/lotes";
import {
  criarPedido,
  type MetodoPagamento,
  type PedidoCriado,
} from "../../api/pedidos";
import { useCurrentUser } from "../../lib/auth-store";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, formatCelular, formatCpfCnpj, money } from "../../lib/format";

import type { PendingOrder } from "./EventoPage";

import styles from "./CheckoutPage.module.css";

const METODOS: { id: MetodoPagamento; l: string; s: string }[] = [
  { id: "PIX", l: "PIX", s: "Aprovação imediata" },
  { id: "CREDIT_CARD", l: "Cartão", s: "até 12x sem juros" },
  { id: "BOLETO", l: "Boleto", s: "1-3 dias úteis" },
];

export const CheckoutPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = useCurrentUser();
  const [ev, setEv] = useState<Evento | null>(null);
  const [lotes, setLotes] = useState<Lote[] | null>(null);
  const [pending] = useState<PendingOrder | null>(() => {
    if (!id) return null;
    const raw = sessionStorage.getItem("pt_pending_order");
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw) as PendingOrder;
      return parsed.eventoId === id ? parsed : null;
    } catch {
      return null;
    }
  });
  const [metodo, setMetodo] = useState<MetodoPagamento>("PIX");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pedidoCriado, setPedidoCriado] = useState<PedidoCriado | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    Promise.all([obterEvento(id), listarLotes(id)])
      .then(([eventoData, lotesData]) => {
        if (cancelled) return;
        setEv(eventoData);
        setLotes(lotesData);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar o evento."));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) return <div className={styles.empty}>{error}</div>;
  if (!ev || !lotes || !pending)
    return <div className={styles.empty}>Carregando…</div>;

  const lotePorId = new Map(lotes.map((l) => [l.id, l] as const));

  const confirmar = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const criado = await criarPedido({
        evento_id: ev.id,
        itens: pending.itens.map((it) => ({
          lote_id: it.loteId,
          quantidade: it.quantidade,
        })),
        metodo,
      });
      setPedidoCriado(criado);
      sessionStorage.removeItem("pt_pending_order");
      // Para PIX, ficamos na tela exibindo o QR. Para boleto/cartão, vai direto
      // para a tela de confirmação com o link da fatura.
      if (criado.pedido.status === "PAGO" || metodo !== "PIX") {
        navigate(`/eventos/${ev.id}/ingressos`, {
          state: { pedidoId: criado.pedido.id, invoiceUrl: criado.invoice_url },
        });
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao criar o pedido."));
    } finally {
      setSubmitting(false);
    }
  };

  const fields = [
    { l: "Nome completo", v: user?.nome ?? "" },
    { l: "CPF", v: user ? formatCpfCnpj(user.cpf_cnpj) : "" },
    { l: "E-mail", v: user?.email ?? "" },
    { l: "Celular", v: user ? formatCelular(user.celular) : "" },
  ];

  return (
    <div className={styles.page}>
      <Link to={`/eventos/${ev.id}`} className={styles.back}>
        ← Voltar
      </Link>
      <h1 className={styles.title}>Finalizar compra</h1>
      <div className={styles.subtitle}>
        {ev.nome} · {dateLong(ev.data_inicio)}
      </div>

      <div className={styles.layout}>
        <div className={styles.column}>
          <section className={styles.card}>
            <h3 className={styles.cardTitle}>1 · Seus dados</h3>
            <div className={styles.fieldGrid}>
              {fields.map((f) => (
                <div key={f.l}>
                  <label className={styles.label}>{f.l}</label>
                  <input
                    className={styles.input}
                    defaultValue={f.v}
                    placeholder={user ? undefined : "Faça login para preencher"}
                    readOnly
                  />
                </div>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h3 className={styles.cardTitle}>2 · Forma de pagamento</h3>
            <div className={styles.metodos}>
              {METODOS.map((m) => (
                <button
                  type="button"
                  key={m.id}
                  className={styles.metodo}
                  data-active={metodo === m.id ? "1" : undefined}
                  onClick={() => setMetodo(m.id)}
                >
                  <div className={styles.metodoLabel}>{m.l}</div>
                  <div className={styles.metodoSub}>{m.s}</div>
                </button>
              ))}
            </div>
            {metodo === "PIX" && (
              <div className={styles.metodoHint}>
                Após confirmar, o QR Code do PIX aparecerá nesta tela.
                Pagamento confirmado em segundos.
              </div>
            )}
            {metodo === "CREDIT_CARD" && (
              <div className={styles.metodoHint}>
                Você será redirecionado para a página segura do Asaas para
                informar os dados do cartão.
              </div>
            )}
            {metodo === "BOLETO" && (
              <div className={styles.metodoHint}>
                O boleto será gerado e enviado para o seu e-mail. Compensação
                em até 3 dias úteis.
              </div>
            )}
          </section>

          {pedidoCriado?.pix_qrcode && (
            <section className={styles.card}>
              <h3 className={styles.cardTitle}>3 · Pague com PIX</h3>
              <div className={styles.pixWrap}>
                <img
                  src={`data:image/png;base64,${pedidoCriado.pix_qrcode.encodedImage}`}
                  alt="QR Code PIX"
                  className={styles.pixQr}
                />
                <div>
                  <div className={styles.metodoHint}>
                    Escaneie o QR Code com o app do seu banco ou copie o código
                    abaixo.
                  </div>
                  <textarea
                    readOnly
                    value={pedidoCriado.pix_qrcode.payload}
                    className={styles.pixPayload}
                  />
                </div>
              </div>
            </section>
          )}
        </div>

        <aside>
          <div className={styles.summary}>
            <h3 className={styles.cardTitle}>Resumo do pedido</h3>
            {pending.itens.map((it) => {
              const lote = lotePorId.get(it.loteId);
              if (!lote) return null;
              return (
                <div key={it.loteId} className={styles.summaryRow}>
                  <span>
                    {it.quantidade} × {lote.nome}
                  </span>
                  <span>{money(it.quantidade * lote.preco)}</span>
                </div>
              );
            })}
            <div className={styles.summaryTotal}>
              <span>Total</span>
              <span>{money(pending.total)}</span>
            </div>
            {error && <div className={styles.errorMsg}>⚠ {error}</div>}
            <button
              type="button"
              className={styles.cta}
              onClick={confirmar}
              disabled={submitting || pedidoCriado !== null}
            >
              {submitting
                ? "Criando pedido…"
                : pedidoCriado
                  ? "Aguardando pagamento"
                  : "Confirmar pagamento"}
            </button>
            <div className={styles.secure}>
              🔒 Conexão segura · Asaas Gateway
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
