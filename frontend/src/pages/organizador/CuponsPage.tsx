import { useEffect, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import {
  criarCupom,
  deletarCupom,
  editarCupom,
  listarCupons,
  type Cupom,
  type CupomCreate,
  type TipoDesconto,
} from "../../api/cupons";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, localToUtcIso, money } from "../../lib/format";

import shared from "./shared.module.css";
import styles from "./orgForms.module.css";

const formatValor = (c: Cupom): string =>
  c.tipo_desconto === "PERCENTUAL"
    ? `${c.valor_desconto}%`
    : money(c.valor_desconto);

export const CuponsPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();
  const [cupons, setCupons] = useState<Cupom[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [tipo, setTipo] = useState<TipoDesconto>("PERCENTUAL");
  const [valor, setValor] = useState("");
  const [quantidadeMaxima, setQuantidadeMaxima] = useState("");
  const [validoAte, setValidoAte] = useState("");
  const [ativo, setAtivo] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    listarCupons(id)
      .then((data) => {
        if (!cancelled) setCupons(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar cupons."));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const toggleAtivo = async (cupom: Cupom) => {
    try {
      const atualizado = await editarCupom(cupom.id, { ativo: !cupom.ativo });
      setCupons((prev) =>
        prev ? prev.map((c) => (c.id === cupom.id ? atualizado : c)) : prev,
      );
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao atualizar cupom."));
    }
  };

  const remover = async (cupom: Cupom) => {
    if (!confirm(`Excluir o cupom "${cupom.codigo}"?`)) return;
    try {
      await deletarCupom(cupom.id);
      setCupons((prev) => (prev ? prev.filter((c) => c.id !== cupom.id) : prev));
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao excluir cupom."));
    }
  };

  const criarNovoCupom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const payload: CupomCreate = {
        codigo,
        tipo_desconto: tipo,
        valor_desconto: parseFloat(valor),
        quantidade_maxima: quantidadeMaxima
          ? parseInt(quantidadeMaxima, 10)
          : null,
        valido_ate: localToUtcIso(validoAte),
        ativo,
      };
      const novo = await criarCupom(id, payload);
      setCupons((prev) => (prev ? [...prev, novo] : [novo]));
      setCodigo("");
      setTipo("PERCENTUAL");
      setValor("");
      setQuantidadeMaxima("");
      setValidoAte("");
      setAtivo(true);
      setShowForm(false);
    } catch (err) {
      setFormError(extractErrorMessage(err, "Falha ao criar cupom."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Cupons`}
        title="Cupons de desconto"
        actions={
          <button
            className={showForm ? shared.btnSecondary : shared.btnPrimary}
            onClick={() => {
              setShowForm((v) => !v);
              setFormError(null);
            }}
          >
            {showForm ? "Cancelar" : "+ Criar cupom"}
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

        {showForm && (
          <div className={shared.cardPadded}>
            <h3 className={shared.cardTitle}>Novo cupom</h3>
            <form className={styles.form} onSubmit={criarNovoCupom}>
              <div className={styles.row}>
                <Field label="Código *">
                  <input
                    className={styles.input}
                    value={codigo}
                    onChange={(e) => setCodigo(e.target.value.toUpperCase())}
                    placeholder="PROMO10"
                    required
                    minLength={3}
                    maxLength={50}
                  />
                </Field>
                <Field label="Tipo de desconto *">
                  <select
                    className={styles.input}
                    value={tipo}
                    onChange={(e) => setTipo(e.target.value as TipoDesconto)}
                    required
                  >
                    <option value="PERCENTUAL">Percentual (%)</option>
                    <option value="VALOR_FIXO">Valor fixo (R$)</option>
                  </select>
                </Field>
              </div>

              <div className={styles.row}>
                <Field
                  label={tipo === "PERCENTUAL" ? "Desconto (%) *" : "Desconto (R$) *"}
                >
                  <input
                    type="number"
                    className={styles.input}
                    value={valor}
                    onChange={(e) => setValor(e.target.value)}
                    placeholder={tipo === "PERCENTUAL" ? "10" : "25.00"}
                    required
                    min="0"
                    step="0.01"
                    max={tipo === "PERCENTUAL" ? "100" : undefined}
                  />
                </Field>
                <Field label="Quantidade máxima (opcional)">
                  <input
                    type="number"
                    className={styles.input}
                    value={quantidadeMaxima}
                    onChange={(e) => setQuantidadeMaxima(e.target.value)}
                    placeholder="Ilimitado"
                    min="1"
                  />
                </Field>
              </div>

              <div className={styles.row}>
                <Field label="Válido até *">
                  <input
                    type="datetime-local"
                    className={styles.input}
                    value={validoAte}
                    onChange={(e) => setValidoAte(e.target.value)}
                    required
                  />
                </Field>
                <Field label=" ">
                  <label className={styles.checkRow}>
                    <input
                      type="checkbox"
                      checked={ativo}
                      onChange={(e) => setAtivo(e.target.checked)}
                    />
                    Ativar imediatamente
                  </label>
                </Field>
              </div>

              {formError && <div className={styles.formError}>⚠ {formError}</div>}

              <div className={styles.formActions}>
                <button
                  type="button"
                  className={shared.btnSecondary}
                  onClick={() => {
                    setShowForm(false);
                    setFormError(null);
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={shared.btnPrimary}
                  disabled={submitting}
                >
                  {submitting ? "Criando…" : "Criar cupom"}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className={shared.card}>
          {cupons === null ? (
            <div className={styles.empty}>Carregando cupons…</div>
          ) : cupons.length === 0 ? (
            <div className={styles.empty}>Nenhum cupom criado ainda.</div>
          ) : (
            <table className={shared.table}>
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Tipo</th>
                  <th className={styles.numeric}>Desconto</th>
                  <th className={styles.numeric}>Usados</th>
                  <th>Validade</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {cupons.map((c) => (
                  <tr key={c.id}>
                    <td className={styles.bold}>{c.codigo}</td>
                    <td>
                      <span className={styles.tipo}>
                        {c.tipo_desconto === "PERCENTUAL" ? "PERCENTUAL" : "VALOR FIXO"}
                      </span>
                    </td>
                    <td className={`${styles.numeric} ${styles.bold}`}>
                      {formatValor(c)}
                    </td>
                    <td className={styles.numeric}>
                      {c.quantidade_usada}
                      {c.quantidade_maxima != null
                        ? `/${c.quantidade_maxima}`
                        : ""}
                    </td>
                    <td className={styles.dim}>{dateLong(c.valido_ate)}</td>
                    <td>
                      <StatusPill status={c.ativo ? "ATIVO" : "RASCUNHO"} />
                    </td>
                    <td className={styles.numeric}>
                      <button
                        className={shared.btnSecondary}
                        onClick={() => toggleAtivo(c)}
                        style={{ marginRight: 6 }}
                      >
                        {c.ativo ? "Desativar" : "Ativar"}
                      </button>
                      <button
                        className={shared.btnSecondary}
                        onClick={() => remover(c)}
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
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
