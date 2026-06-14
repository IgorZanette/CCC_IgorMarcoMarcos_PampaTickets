import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { obterEvento, type Evento } from "../../api/eventos";
import { listarLotes, type Lote } from "../../api/lotes";
import { criarPedido, type MetodoPagamento } from "../../api/pedidos";
import { validarCupom, type CupomValidacao } from "../../api/cupons";
import { useCurrentUser } from "../../lib/auth-store";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, formatCelular, formatCpfCnpj, money } from "../../lib/format";
import { avaliarLote } from "../../lib/lote";

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

  const [cupomCodigo, setCupomCodigo] = useState(pending?.cupomCodigo ?? "");
  const [cupom, setCupom] = useState<CupomValidacao | null>(null);
  const [cupomErro, setCupomErro] = useState<string | null>(null);
  const [validandoCupom, setValidandoCupom] = useState(false);

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

  // Revalida automaticamente um cupom trazido da tela do evento, para já exibir
  // o desconto sem o participante precisar redigitar e clicar em "Aplicar".
  useEffect(() => {
    if (!ev || !lotes || !pending?.cupomCodigo) return;
    const subtotal = pending.itens.reduce((acc, it) => {
      const lote = lotes.find((l) => l.id === it.loteId);
      return acc + (lote ? lote.preco * it.quantidade : 0);
    }, 0);
    if (subtotal <= 0) return;
    let cancelled = false;
    validarCupom(ev.id, pending.cupomCodigo, subtotal)
      .then((v) => {
        if (!cancelled) setCupom(v);
      })
      .catch((err) => {
        if (!cancelled)
          setCupomErro(extractErrorMessage(err, "Não foi possível validar o cupom."));
      });
    return () => {
      cancelled = true;
    };
  }, [ev, lotes, pending]);

  if (error) return <div className={styles.empty}>{error}</div>;
  if (!ev || !lotes || !pending)
    return <div className={styles.empty}>Carregando…</div>;

  const lotePorId = new Map(lotes.map((l) => [l.id, l] as const));

  const subtotal = pending.itens.reduce((acc, it) => {
    const lote = lotePorId.get(it.loteId);
    return acc + (lote ? lote.preco * it.quantidade : 0);
  }, 0);
  const totalComDesconto = cupom ? cupom.valor_final : subtotal;

  // Lotes carregados frescos no load — revalida disponibilidade aqui também: um lote
  // pode ter expirado ou esgotado entre a seleção e o pagamento. Bloqueia o envio
  // com aviso amigável em vez de deixar o backend recusar com 409.
  const itensIndisponiveis = pending.itens.flatMap((it) => {
    const lote = lotePorId.get(it.loteId);
    if (!lote) return [{ nome: "Ingresso", motivo: "Não está mais disponível" }];
    const disp = avaliarLote(lote);
    if (!disp.disponivel)
      return [{ nome: lote.nome, motivo: disp.rotulo ?? "Indisponível" }];
    if (it.quantidade > disp.restantes)
      return [{ nome: lote.nome, motivo: `Restam apenas ${disp.restantes}` }];
    return [];
  });
  const bloqueado = itensIndisponiveis.length > 0;

  const aplicarCupom = async () => {
    if (subtotal <= 0) return;
    setValidandoCupom(true);
    setCupomErro(null);
    try {
      const validado = await validarCupom(ev.id, cupomCodigo.trim(), subtotal);
      setCupom(validado);
    } catch (err) {
      setCupom(null);
      setCupomErro(extractErrorMessage(err, "Não foi possível validar o cupom."));
    } finally {
      setValidandoCupom(false);
    }
  };

  const removerCupom = () => {
    setCupom(null);
    setCupomCodigo("");
    setCupomErro(null);
  };

  const confirmar = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    if (bloqueado) return;
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
        cupom_codigo: cupom?.codigo ?? null,
      });
      sessionStorage.removeItem("pt_pending_order");
      // Vai para a tela de status, que mostra QR/fatura enquanto pendente e faz
      // polling até o webhook do Asaas confirmar (ou recusar) o pagamento.
      navigate(`/eventos/${ev.id}/pagamento/${criado.pedido.id}`, {
        state: {
          invoiceUrl: criado.invoice_url,
          pixQrcode: criado.pix_qrcode,
          boleto: criado.boleto,
        },
      });
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
                Após confirmar, você verá o QR Code do PIX e acompanhará a
                confirmação do pagamento em tempo real.
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
            <div className={styles.cupomBox}>
              <div className={styles.label}>Cupom de desconto</div>
              {cupom ? (
                <div className={styles.cupomAplicado}>
                  <span>
                    ✓ <strong>{cupom.codigo}</strong> aplicado
                  </span>
                  <button
                    type="button"
                    className={styles.cupomRemover}
                    onClick={removerCupom}
                    disabled={submitting}
                  >
                    Remover
                  </button>
                </div>
              ) : (
                <div className={styles.cupomRow}>
                  <input
                    className={styles.input}
                    value={cupomCodigo}
                    onChange={(e) => setCupomCodigo(e.target.value.toUpperCase())}
                    placeholder="Digite o código"
                    disabled={submitting}
                  />
                  <button
                    type="button"
                    className={styles.cupomBtn}
                    onClick={aplicarCupom}
                    disabled={!cupomCodigo.trim() || validandoCupom || submitting}
                  >
                    {validandoCupom ? "…" : "Aplicar"}
                  </button>
                </div>
              )}
              {cupomErro && <div className={styles.cupomErro}>⚠ {cupomErro}</div>}
            </div>

            {cupom && (
              <>
                <div className={styles.summaryRow}>
                  <span className={styles.summaryDim}>Subtotal</span>
                  <span>{money(subtotal)}</span>
                </div>
                <div className={styles.summaryRow}>
                  <span className={styles.summaryDim}>Desconto</span>
                  <span>−{money(cupom.valor_desconto_aplicado)}</span>
                </div>
              </>
            )}

            <div className={styles.summaryTotal}>
              <span>Total</span>
              <span>{money(totalComDesconto)}</span>
            </div>
            {bloqueado && (
              <div className={styles.errorMsg}>
                ⚠ Alguns itens não estão mais disponíveis:
                {itensIndisponiveis.map((it, i) => (
                  <div key={i}>
                    • {it.nome} — {it.motivo}
                  </div>
                ))}
                <Link to={`/eventos/${ev.id}`} className={styles.back}>
                  ← Revisar ingressos
                </Link>
              </div>
            )}
            {error && <div className={styles.errorMsg}>⚠ {error}</div>}
            <button
              type="button"
              className={styles.cta}
              onClick={confirmar}
              disabled={submitting || bloqueado}
            >
              {submitting ? "Criando pedido…" : "Confirmar pagamento"}
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
