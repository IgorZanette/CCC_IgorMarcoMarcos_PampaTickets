import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { criarEvento, gradientFor, type Evento } from "../../api/eventos";
import { PageHeader } from "../../components/PageHeader";
import { setActiveEventId } from "../../lib/active-event";
import { extractErrorMessage } from "../../lib/errors";

import shared from "./shared.module.css";
import styles from "./CreateEventPage.module.css";

export const CreateEventPage = () => {
  const navigate = useNavigate();
  const [nome, setNome] = useState("");
  const [descricao, setDescricao] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [local, setLocal] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const previewId = nome || "preview";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const novo: Evento = await criarEvento({
        nome,
        descricao: descricao || null,
        data_inicio: dataInicio,
        data_fim: dataFim,
        local,
      });
      setActiveEventId(novo.id);
      navigate("/organizador/evento");
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao criar o evento."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb="Eventos / Novo evento"
        title="Criar evento"
        actions={
          <button
            className={shared.btnSecondary}
            onClick={() => navigate("/organizador")}
            type="button"
          >
            Cancelar
          </button>
        }
      />

      <div className={shared.body}>
        <div className={styles.layout}>
          <form className={shared.cardPadded} onSubmit={submit}>
            <h2 className={styles.heading}>Conte sobre o evento</h2>
            <p className={styles.lead}>
              O evento é criado como <strong>RASCUNHO</strong>. Você pode
              configurar lotes e publicar depois.
            </p>

            <Field label="Nome do evento *">
              <input
                className={styles.input}
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Festival de Inverno 2026"
                required
                minLength={3}
                maxLength={255}
              />
            </Field>

            <Field label="Descrição">
              <textarea
                className={styles.textarea}
                rows={4}
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Conte o que torna esse evento único…"
              />
            </Field>

            <div className={styles.row}>
              <Field label="Início *">
                <input
                  type="datetime-local"
                  className={styles.input}
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                  required
                />
              </Field>
              <Field label="Encerramento *">
                <input
                  type="datetime-local"
                  className={styles.input}
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                  required
                />
              </Field>
            </div>

            <Field label="Local *">
              <input
                className={styles.input}
                value={local}
                onChange={(e) => setLocal(e.target.value)}
                placeholder="Parque Farroupilha, Porto Alegre, RS"
                required
                minLength={3}
                maxLength={500}
              />
            </Field>

            {error && (
              <div
                style={{
                  marginTop: 12,
                  padding: "10px 12px",
                  background: "rgba(200, 16, 46, 0.08)",
                  color: "#c8102e",
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                ⚠ {error}
              </div>
            )}

            <div className={styles.formActions}>
              <button
                type="button"
                className={shared.btnSecondary}
                onClick={() => navigate("/organizador")}
              >
                ← Cancelar
              </button>
              <button
                type="submit"
                className={shared.btnPrimary}
                disabled={submitting}
              >
                {submitting ? "Criando…" : "Criar evento (RASCUNHO)"}
              </button>
            </div>
          </form>

          <aside>
            <div className={styles.preview}>
              <div className={styles.previewHead}>👁 Preview</div>
              <div
                className={styles.previewCover}
                style={{ background: gradientFor(previewId) }}
              />
              <div className={styles.previewBody}>
                <div className={styles.previewTitle}>
                  {nome || "Nome do evento"}
                </div>
                <div className={styles.previewMeta}>
                  📅 {dataInicio || "Data de início"}
                </div>
                <div className={styles.previewMeta}>
                  📍 {local || "Local"}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
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
