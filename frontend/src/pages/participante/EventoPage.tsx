import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  cidadeFromLocal,
  gradientFor,
  obterEvento,
  type Evento,
} from "../../api/eventos";
import { listarLotes, type Lote } from "../../api/lotes";
import { extractErrorMessage } from "../../lib/errors";
import { dateFull, money } from "../../lib/format";

import styles from "./EventoPage.module.css";

export type PendingOrder = {
  eventoId: string;
  itens: { loteId: string; quantidade: number }[];
  total: number;
};

export const EventoPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ev, setEv] = useState<Evento | null>(null);
  const [lotes, setLotes] = useState<Lote[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, number>>({});

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

  const totals = useMemo(() => {
    if (!lotes) return { qty: 0, subtotal: 0 };
    let qty = 0;
    let subtotal = 0;
    lotes.forEach((l) => {
      const n = selected[l.id] ?? 0;
      qty += n;
      subtotal += n * l.preco;
    });
    return { qty, subtotal };
  }, [lotes, selected]);

  if (error) {
    return <div className={styles.empty}>{error}</div>;
  }

  if (!ev || !lotes) {
    return <div className={styles.empty}>Carregando evento…</div>;
  }

  const d = dateFull(ev.data_inicio);
  const total = totals.subtotal;

  const checkout = () => {
    const pending: PendingOrder = {
      eventoId: ev.id,
      itens: Object.entries(selected)
        .filter(([, n]) => n > 0)
        .map(([loteId, n]) => ({ loteId, quantidade: n })),
      total,
    };
    sessionStorage.setItem("pt_pending_order", JSON.stringify(pending));
    navigate(`/eventos/${ev.id}/checkout`);
  };

  return (
    <>
      <div className={styles.cover} style={{ background: gradientFor(ev.id) }}>
        <div className={styles.coverOverlay} />
        <div className={styles.coverContent}>
          <div className={styles.dateBlock}>
            <div className={styles.dateMes}>{d.mes}</div>
            <div className={styles.dateDia}>{d.dia}</div>
            <div className={styles.dateSub}>
              {d.semana} · {d.hora}
            </div>
          </div>
          <div>
            <h1 className={styles.title}>{ev.nome}</h1>
            <div className={styles.location}>
              📍 {ev.local} · {cidadeFromLocal(ev.local)}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.layout}>
        <div>
          <h2 className={styles.heading}>Sobre o evento</h2>
          <p className={styles.lead}>{ev.descricao ?? "Sem descrição cadastrada."}</p>

          <h2 className={styles.heading} style={{ marginTop: 24 }}>
            Selecione seus ingressos
          </h2>
          <div className={styles.lotes}>
            {lotes.length === 0 && (
              <div className={styles.empty}>Nenhum lote disponível.</div>
            )}
            {lotes.map((l) => {
              const restantes = l.quantidade_disponivel;
              const inativo = !l.ativo;
              const esgotado = restantes === 0;
              const indisponivel = inativo || esgotado;
              const acabando =
                !indisponivel && restantes / l.quantidade_total < 0.1;
              const qty = selected[l.id] ?? 0;
              return (
                <div
                  key={l.id}
                  className={styles.lote}
                  data-selected={qty > 0 ? "1" : undefined}
                  data-esgotado={indisponivel ? "1" : undefined}
                >
                  <div className={styles.loteInfo}>
                    <div className={styles.loteNome}>{l.nome}</div>
                    {acabando && (
                      <div className={styles.loteWarn}>
                        ⚠ Apenas {restantes} restantes
                      </div>
                    )}
                    {esgotado && (
                      <div className={styles.loteEsgotado}>Esgotado</div>
                    )}
                    {inativo && !esgotado && (
                      <div className={styles.loteEsgotado}>Indisponível</div>
                    )}
                  </div>
                  <div className={styles.lotePreco}>{money(l.preco)}</div>
                  {!indisponivel && (
                    <div className={styles.qtyControls}>
                      <button
                        type="button"
                        className={styles.qtyBtn}
                        onClick={() =>
                          setSelected((s) => ({
                            ...s,
                            [l.id]: Math.max(0, (s[l.id] ?? 0) - 1),
                          }))
                        }
                        aria-label="Remover"
                      >
                        −
                      </button>
                      <div className={styles.qtyValue}>{qty}</div>
                      <button
                        type="button"
                        className={styles.qtyBtnPrimary}
                        onClick={() =>
                          setSelected((s) => ({
                            ...s,
                            [l.id]: Math.min(restantes, (s[l.id] ?? 0) + 1),
                          }))
                        }
                        aria-label="Adicionar"
                      >
                        +
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <aside>
          <div className={styles.sidebar}>
            <div className={styles.sidebarTitle}>{ev.nome}</div>
            <div className={styles.sidebarRow}>
              <span className={styles.sidebarLabel}>
                {totals.qty} ingresso{totals.qty !== 1 ? "s" : ""}
              </span>
              <span>{money(totals.subtotal)}</span>
            </div>
            <div className={styles.sidebarTotal}>
              <span>Total</span>
              <span>{money(total)}</span>
            </div>
            <button
              type="button"
              className={styles.cta}
              disabled={totals.qty === 0}
              onClick={checkout}
            >
              {totals.qty > 0
                ? "Continuar para pagamento →"
                : "Selecione ingressos"}
            </button>
            <div className={styles.secure}>
              🔒 Pagamento seguro · PIX, cartão ou boleto
            </div>
          </div>
        </aside>
      </div>
    </>
  );
};
