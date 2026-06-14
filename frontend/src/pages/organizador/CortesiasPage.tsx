import { useEffect, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import {
  cancelarCortesia,
  emitirCortesia,
  listarCortesias,
  type Cortesia,
  type CortesiaCreate,
} from "../../api/cortesias";
import { listarLotesOrganizador, type Lote } from "../../api/lotes";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { EmptyState } from "../../components/EmptyState";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong } from "../../lib/format";
import { toastError, toastSuccess } from "../../lib/toast";

import shared from "./shared.module.css";
import styles from "./orgForms.module.css";

export const CortesiasPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();
  const [cortesias, setCortesias] = useState<Cortesia[] | null>(null);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [loteId, setLoteId] = useState("");
  const [email, setEmail] = useState("");
  const [motivo, setMotivo] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cortesiaCancelar, setCortesiaCancelar] = useState<Cortesia | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    Promise.all([listarCortesias(id), listarLotesOrganizador(id)])
      .then(([cs, ls]) => {
        if (cancelled) return;
        setCortesias(cs);
        setLotes(ls);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar cortesias."));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const confirmarCancelamento = async () => {
    if (!cortesiaCancelar) return;
    await cancelarCortesia(cortesiaCancelar.id);
    setCortesias((prev) =>
      prev ? prev.filter((c) => c.id !== cortesiaCancelar.id) : prev,
    );
    toastSuccess("Cortesia cancelada.");
  };

  const emitirNova = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    try {
      const payload: CortesiaCreate = {
        lote_id: loteId,
        email_beneficiado: email,
        motivo: motivo || null,
      };
      const nova = await emitirCortesia(id, payload);
      setCortesias((prev) => (prev ? [nova, ...prev] : [nova]));
      setLoteId("");
      setEmail("");
      setMotivo("");
      setShowForm(false);
      toastSuccess("Cortesia emitida!");
    } catch (err) {
      toastError(err, "Falha ao emitir cortesia.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Cortesias`}
        title="Cortesias"
        actions={
          <button
            className={shared.btnPrimary}
            onClick={() => setShowForm(true)}
            disabled={lotes.length === 0}
            title={
              lotes.length === 0
                ? "Crie ao menos um lote antes de emitir cortesias"
                : undefined
            }
          >
            + Emitir cortesia
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
          labelledBy="nova-cortesia-titulo"
          size="lg"
        >
          <h3 id="nova-cortesia-titulo" className={shared.cardTitle}>
            Nova cortesia
          </h3>
          <p style={{ marginTop: 6, marginBottom: 4 }} className={styles.dim}>
            O e-mail informado precisa pertencer a um participante já cadastrado.
          </p>
          <form className={styles.form} onSubmit={emitirNova}>
              <div className={styles.row}>
                <Field label="Lote *">
                  <select
                    className={styles.input}
                    value={loteId}
                    onChange={(e) => setLoteId(e.target.value)}
                    required
                  >
                    <option value="" disabled>
                      Selecione um lote
                    </option>
                    {lotes.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.nome}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="E-mail do beneficiado *">
                  <input
                    type="email"
                    className={styles.input}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="participante@email.com"
                    required
                  />
                </Field>
              </div>

              <Field label="Motivo (opcional)">
                <input
                  className={styles.input}
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  placeholder="Patrocinador da edição 2026"
                  maxLength={500}
                />
              </Field>

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
                  {submitting ? "Emitindo…" : "Emitir cortesia"}
                </button>
              </div>
            </form>
        </Modal>

        <div className={shared.card}>
          {cortesias === null ? (
            <div className={styles.empty}>Carregando cortesias…</div>
          ) : cortesias.length === 0 ? (
            <EmptyState
              icon="✦"
              title="Nenhuma cortesia emitida ainda"
              hint="Emita cortesias para convidados, patrocinadores e parceiros do evento."
              action={
                lotes.length > 0 ? (
                  <button
                    className={shared.btnPrimary}
                    onClick={() => setShowForm(true)}
                  >
                    + Emitir cortesia
                  </button>
                ) : undefined
              }
            />
          ) : (
            <table className={shared.table}>
              <thead>
                <tr>
                  <th>Beneficiado</th>
                  <th>Lote</th>
                  <th>Emitida em</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {cortesias.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div className={styles.bold}>{c.beneficiado_nome}</div>
                      <div className={styles.dim}>{c.beneficiado_email}</div>
                    </td>
                    <td>
                      <span className={styles.tipo}>{c.lote_nome}</span>
                    </td>
                    <td className={styles.dim}>{dateLong(c.emitida_em)}</td>
                    <td>
                      <StatusPill
                        status={c.ingresso_id ? "ATIVO" : "PENDENTE"}
                      />
                    </td>
                    <td className={styles.numeric}>
                      <button
                        className={shared.btnSecondary}
                        onClick={() => setCortesiaCancelar(c)}
                      >
                        Cancelar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={cortesiaCancelar !== null}
        title="Cancelar cortesia"
        message={
          <>
            Cancelar a cortesia de{" "}
            <strong>{cortesiaCancelar?.beneficiado_nome}</strong>? O ingresso
            associado será invalidado.
          </>
        }
        confirmLabel="Cancelar cortesia"
        cancelLabel="Voltar"
        danger
        onConfirm={confirmarCancelamento}
        onClose={() => setCortesiaCancelar(null)}
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
