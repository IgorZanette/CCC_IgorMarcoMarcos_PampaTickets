import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  ativarLote,
  deletarLote,
  desativarLote,
  listarLotesOrganizador,
  type Lote,
} from "../../api/lotes";
import { PageHeader } from "../../components/PageHeader";
import { ProgressBar } from "../../components/ProgressBar";
import { StatusPill } from "../../components/StatusPill";
import { useActiveEvent } from "../../lib/active-event";
import { extractErrorMessage } from "../../lib/errors";
import { money } from "../../lib/format";

import shared from "./shared.module.css";
import styles from "./LotesPage.module.css";

export const LotesPage = () => {
  const { evento } = useActiveEvent();
  const [lotes, setLotes] = useState<Lote[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!evento) return;
    let cancelled = false;
    listarLotesOrganizador(evento.id)
      .then((data) => {
        if (!cancelled) setLotes(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar lotes."));
      });
    return () => {
      cancelled = true;
    };
  }, [evento]);

  const toggleAtivo = async (lote: Lote) => {
    try {
      const atualizado = lote.ativo
        ? await desativarLote(lote.id)
        : await ativarLote(lote.id);
      setLotes((prev) =>
        prev ? prev.map((l) => (l.id === lote.id ? atualizado : l)) : prev,
      );
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao atualizar lote."));
    }
  };

  const remover = async (lote: Lote) => {
    if (!confirm(`Excluir o lote "${lote.nome}"?`)) return;
    try {
      await deletarLote(lote.id);
      setLotes((prev) => (prev ? prev.filter((l) => l.id !== lote.id) : prev));
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao excluir lote."));
    }
  };

  if (!evento) {
    return (
      <div className={shared.body}>
        <div className={shared.cardPadded}>
          <h3 className={shared.cardTitle}>Nenhum evento selecionado</h3>
          <p style={{ marginTop: 8, color: "var(--pt-org-text-dim)" }}>
            Volte para o painel e escolha um evento para gerenciar lotes.
          </p>
          <Link
            to="/organizador"
            className={shared.btnPrimary}
            style={{ marginTop: 16, display: "inline-block" }}
          >
            Ir para o painel →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        breadcrumb={`${evento.nome} / Lotes & vendas`}
        title="Lotes & vendas"
        actions={
          <button className={shared.btnPrimary} disabled>
            + Criar lote
          </button>
        }
      />

      <div className={shared.body}>
        {error && (
          <div
            className={shared.cardPadded}
            style={{ borderColor: "#c8102e", color: "#c8102e", marginBottom: 16 }}
          >
            ⚠ {error}
          </div>
        )}

        <div className={shared.card}>
          {lotes === null ? (
            <div style={{ padding: 32, textAlign: "center", color: "var(--pt-org-text-dim)" }}>
              Carregando lotes…
            </div>
          ) : lotes.length === 0 ? (
            <div style={{ padding: 32, textAlign: "center", color: "var(--pt-org-text-dim)" }}>
              Nenhum lote criado ainda.
            </div>
          ) : (
            <table className={shared.table}>
              <thead>
                <tr>
                  <th>Lote</th>
                  <th>Tipo</th>
                  <th className={styles.numeric}>Preço</th>
                  <th className={styles.numeric}>Vendidos</th>
                  <th style={{ width: 220 }}>Progresso</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {lotes.map((l) => {
                  const pct = l.quantidade_total
                    ? l.quantidade_vendida / l.quantidade_total
                    : 0;
                  const esgotado = l.quantidade_disponivel === 0;
                  const status = !l.ativo
                    ? "RASCUNHO"
                    : esgotado
                      ? "ESGOTADO"
                      : "VENDENDO";
                  return (
                    <tr key={l.id}>
                      <td className={styles.bold}>{l.nome}</td>
                      <td>
                        <span className={styles.tipo}>{l.tipo}</span>
                      </td>
                      <td className={`${styles.numeric} ${styles.bold}`}>
                        {money(l.preco)}
                      </td>
                      <td className={styles.numeric}>
                        {l.quantidade_vendida.toLocaleString("pt-BR")}/
                        {l.quantidade_total.toLocaleString("pt-BR")}
                      </td>
                      <td>
                        <ProgressBar value={pct} />
                        <div className={styles.pct}>{(pct * 100).toFixed(0)}%</div>
                      </td>
                      <td>
                        <StatusPill status={status} />
                      </td>
                      <td className={styles.numeric}>
                        <button
                          className={shared.btnSecondary}
                          onClick={() => toggleAtivo(l)}
                          style={{ marginRight: 6 }}
                        >
                          {l.ativo ? "Desativar" : "Ativar"}
                        </button>
                        <button
                          className={shared.btnSecondary}
                          onClick={() => remover(l)}
                          disabled={l.quantidade_vendida > 0}
                          title={
                            l.quantidade_vendida > 0
                              ? "Lote com vendas não pode ser excluído"
                              : "Excluir lote"
                          }
                        >
                          Excluir
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
};
