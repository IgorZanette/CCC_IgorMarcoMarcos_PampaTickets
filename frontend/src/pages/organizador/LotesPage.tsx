import { useEffect, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import {
  ativarLote,
  criarLote,
  deletarLote,
  desativarLote,
  listarLotesOrganizador,
  type Lote,
  type LoteCreate,
  type TipoLote,
} from "../../api/lotes";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { EmptyState } from "../../components/EmptyState";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { ProgressBar } from "../../components/ProgressBar";
import { StatusPill } from "../../components/StatusPill";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { localToUtcIso, money } from "../../lib/format";
import { toastError, toastSuccess } from "../../lib/toast";

import shared from "./shared.module.css";
import styles from "./LotesPage.module.css";

export const LotesPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();
  const [lotes, setLotes] = useState<Lote[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Estado do formulário
  const [showForm, setShowForm] = useState(false);
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState<TipoLote>("INTEIRA");
  const [preco, setPreco] = useState("");
  const [quantidade, setQuantidade] = useState("");
  const [inicio, setInicio] = useState("");
  const [fim, setFim] = useState("");
  const [ativo, setAtivo] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  // Lote alvo do diálogo de exclusão (null = fechado).
  const [loteExcluir, setLoteExcluir] = useState<Lote | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    listarLotesOrganizador(id)
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
  }, [id]);

  const toggleAtivo = async (lote: Lote) => {
    try {
      const atualizado = lote.ativo
        ? await desativarLote(lote.id)
        : await ativarLote(lote.id);
      setLotes((prev) =>
        prev ? prev.map((l) => (l.id === lote.id ? atualizado : l)) : prev,
      );
      toastSuccess(atualizado.ativo ? "Lote ativado." : "Lote desativado.");
    } catch (err) {
      toastError(err, "Falha ao atualizar lote.");
    }
  };

  const confirmarExclusao = async () => {
    if (!loteExcluir) return;
    await deletarLote(loteExcluir.id);
    setLotes((prev) =>
      prev ? prev.filter((l) => l.id !== loteExcluir.id) : prev,
    );
    toastSuccess("Lote excluído.");
  };

  const criarNovoLote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    try {
      const payload: LoteCreate = {
        nome,
        tipo,
        preco: parseFloat(preco),
        quantidade_total: parseInt(quantidade, 10),
        data_inicio_venda: localToUtcIso(inicio),
        data_fim_venda: localToUtcIso(fim),
        ativo,
      };
      const novo = await criarLote(id, payload);
      setLotes((prev) => (prev ? [...prev, novo] : [novo]));
      setNome("");
      setTipo("INTEIRA");
      setPreco("");
      setQuantidade("");
      setInicio("");
      setFim("");
      setAtivo(true);
      setShowForm(false);
      toastSuccess("Lote criado!");
    } catch (err) {
      toastError(err, "Falha ao criar lote.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Lotes & vendas`}
        title="Lotes & vendas"
        actions={
          <button className={shared.btnPrimary} onClick={() => setShowForm(true)}>
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

        <Modal
          open={showForm}
          onClose={() => setShowForm(false)}
          locked={submitting}
          labelledBy="novo-lote-titulo"
          size="lg"
        >
          <h3 id="novo-lote-titulo" className={shared.cardTitle}>
            Novo lote
          </h3>
          <form className={styles.form} onSubmit={criarNovoLote}>
              <Field label="Nome do lote *">
                <input
                  className={styles.input}
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="1º Lote — Pista"
                  required
                  minLength={2}
                  maxLength={255}
                />
              </Field>

              <div className={styles.row}>
                <Field label="Tipo *">
                  <select
                    className={styles.input}
                    value={tipo}
                    onChange={(e) => setTipo(e.target.value as TipoLote)}
                    required
                  >
                    <option value="INTEIRA">Inteira</option>
                    <option value="MEIA">Meia-entrada</option>
                    <option value="PROMOCIONAL">Promocional</option>
                  </select>
                </Field>
                <Field label="Preço (R$) *">
                  <input
                    type="number"
                    className={styles.input}
                    value={preco}
                    onChange={(e) => setPreco(e.target.value)}
                    placeholder="120.00"
                    required
                    min="0"
                    step="0.01"
                  />
                </Field>
              </div>

              <div className={styles.row}>
                <Field label="Quantidade total *">
                  <input
                    type="number"
                    className={styles.input}
                    value={quantidade}
                    onChange={(e) => setQuantidade(e.target.value)}
                    placeholder="500"
                    required
                    min="1"
                  />
                </Field>
                <Field label=" ">
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={ativo}
                      onChange={(e) => setAtivo(e.target.checked)}
                    />
                    Ativar imediatamente para venda
                  </label>
                </Field>
              </div>

              <div className={styles.row}>
                <Field label="Início das vendas *">
                  <input
                    type="datetime-local"
                    className={styles.input}
                    value={inicio}
                    onChange={(e) => setInicio(e.target.value)}
                    required
                  />
                </Field>
                <Field label="Fim das vendas *">
                  <input
                    type="datetime-local"
                    className={styles.input}
                    value={fim}
                    onChange={(e) => setFim(e.target.value)}
                    required
                  />
                </Field>
              </div>

              <div className={styles.formActions}>
                <button
                  type="button"
                  className={shared.btnSecondary}
                  onClick={() => setShowForm(false)}
                  disabled={submitting}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={shared.btnPrimary}
                  disabled={submitting}
                >
                  {submitting ? "Criando…" : "Criar lote"}
                </button>
              </div>
            </form>
        </Modal>

        <div className={shared.card}>
          {lotes === null ? (
            <div style={{ padding: 32, textAlign: "center", color: "var(--pt-org-text-dim)" }}>
              Carregando lotes…
            </div>
          ) : lotes.length === 0 ? (
            <EmptyState
              icon="🎟"
              title="Nenhum lote criado ainda"
              hint="Crie o primeiro lote para começar a vender ingressos deste evento."
              action={
                <button
                  className={shared.btnPrimary}
                  onClick={() => setShowForm(true)}
                >
                  + Criar lote
                </button>
              }
            />
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
                          onClick={() => setLoteExcluir(l)}
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

      <ConfirmDialog
        open={loteExcluir !== null}
        title="Excluir lote"
        message={
          <>
            Tem certeza que deseja excluir o lote{" "}
            <strong>{loteExcluir?.nome}</strong>? Essa ação não pode ser desfeita.
          </>
        }
        confirmLabel="Excluir"
        danger
        onConfirm={confirmarExclusao}
        onClose={() => setLoteExcluir(null)}
      />
    </>
  );
};

const Field = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <div className={styles.field}>
    <div className={styles.fieldLabel}>{label}</div>
    {children}
  </div>
);
