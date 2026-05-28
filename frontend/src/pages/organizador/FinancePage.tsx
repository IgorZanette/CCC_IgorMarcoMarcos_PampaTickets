import { Link } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";

import shared from "./shared.module.css";

export const FinancePage = () => (
  <>
    <PageHeader breadcrumb="Painel / Financeiro" title="Financeiro" />

    <div className={shared.body}>
      <div className={shared.cardPadded}>
        <h3 className={shared.cardTitle}>UC14 — Relatório financeiro</h3>
        <p
          style={{
            marginTop: 12,
            color: "var(--pt-org-text-dim)",
            lineHeight: 1.6,
          }}
        >
          O relatório financeiro consolidado (receita, ticket médio, estornos,
          ocupação por lote) ainda não foi implementado no backend. Quando o
          endpoint estiver disponível, ele aparecerá aqui com opção de exportar
          o PDF gerado pelo bucket <code>relatorios/</code> no Supabase Storage.
        </p>
        <Link
          to="/organizador"
          className={shared.btnSecondary}
          style={{ marginTop: 20, display: "inline-block" }}
        >
          ← Voltar para visão geral
        </Link>
      </div>
    </div>
  </>
);
