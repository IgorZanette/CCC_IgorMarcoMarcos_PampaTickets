import { Link } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";
import { useActiveEvent } from "../../lib/active-event";

import shared from "./shared.module.css";

export const AttendeesPage = () => {
  const { evento } = useActiveEvent();

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Participantes`}
        title="Participantes"
      />

      <div className={shared.body}>
        <div className={shared.cardPadded}>
          <h3 className={shared.cardTitle}>Lista de participantes</h3>
          <p
            style={{
              marginTop: 12,
              color: "var(--pt-org-text-dim)",
              lineHeight: 1.6,
            }}
          >
            Ainda não existe endpoint no backend para o organizador listar
            ingressos vendidos de um evento. Hoje só o participante vê os
            próprios ingressos via <code>GET /api/ingressos/meus</code>. Quando
            for criada uma rota tipo{" "}
            <code>GET /api/organizador/eventos/:id/ingressos</code>, esta tela
            vai listar nome, e-mail, lote e status (ATIVO / UTILIZADO /
            CANCELADO) com busca e filtros.
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
};
