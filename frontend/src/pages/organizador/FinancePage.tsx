import { useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import { baixarRelatorio } from "../../api/eventos";
import { Icon } from "../../components/Icon";
import { PageHeader } from "../../components/PageHeader";
import { LoadingBlock } from "../../components/Spinner";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";

import shared from "./shared.module.css";

export const FinancePage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento, loading, error: notFound } = useOutletContext<OrgOutlet>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    if (!id) return;
    setBusy(true);
    setError(null);
    try {
      await baixarRelatorio(id);
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao gerar o relatório."));
    } finally {
      setBusy(false);
    }
  };

  if (loading && !evento) {
    return (
      <>
        <PageHeader breadcrumb="Financeiro" title="Financeiro" />
        <div className={shared.body}>
          <LoadingBlock message="Carregando financeiro…" />
        </div>
      </>
    );
  }

  if (!evento || notFound) {
    return (
      <>
        <PageHeader breadcrumb="Financeiro" title="Financeiro" />
        <div className={shared.body}>
          <div className={shared.cardPadded}>
            <h3 className={shared.cardTitle}>Evento não encontrado</h3>
            <p style={{ marginTop: 8, color: "var(--pt-org-text-dim)" }}>
              Este evento não existe ou você não tem acesso a ele.
            </p>
            <Link
              to="/organizador"
              className={shared.btnSecondary}
              style={{ marginTop: 16, display: "inline-block" }}
            >
              ← Todos os eventos
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader breadcrumb={`${evento.nome} / Financeiro`} title="Financeiro" />

      <div className={shared.body}>
        {error && (
          <div
            className={shared.cardPadded}
            style={{ borderColor: "#c8102e", color: "#c8102e", marginBottom: 16 }}
          >
            <Icon name="warning" /> {error}
          </div>
        )}

        <div className={shared.cardPadded}>
          <div className={shared.eyebrow}>Evento</div>
          <h3 className={shared.cardTitle} style={{ marginTop: 4 }}>
            {evento.nome}
          </h3>

          <p style={{ marginTop: 12, color: "var(--pt-org-text-dim)", lineHeight: 1.6 }}>
            Gere o relatório financeiro completo deste evento em PDF. Ele inclui
            receita bruta, descontos de cupons, cortesias, reembolsos, receita
            líquida e taxa de comparecimento por lote.
          </p>

          <div style={{ marginTop: 20, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <button
              className={shared.btnPrimary}
              onClick={handleDownload}
              disabled={busy}
            >
              {busy ? "Gerando…" : "Baixar relatório PDF"}
            </button>
            <Link to={`/organizador/eventos/${id}`} className={shared.btnSecondary}>
              ← Voltar para o evento
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};
