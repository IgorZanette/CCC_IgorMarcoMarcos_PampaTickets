import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  gradientFor,
  listarEventosOrganizador,
  type Evento,
} from "../../api/eventos";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import {
  getActiveEventId,
  setActiveEventId,
} from "../../lib/active-event";
import { firstName, useCurrentUser } from "../../lib/auth-store";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong } from "../../lib/format";

import styles from "./DashboardPage.module.css";

const greeting = (): string => {
  const h = new Date().getHours();
  if (h < 12) return "Bom dia";
  if (h < 18) return "Boa tarde";
  return "Boa noite";
};

export const DashboardPage = () => {
  const navigate = useNavigate();
  const user = useCurrentUser();
  const [eventos, setEventos] = useState<Evento[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(getActiveEventId());

  useEffect(() => {
    let cancelled = false;
    listarEventosOrganizador()
      .then((data) => {
        if (cancelled) return;
        setEventos(data);
        if (!getActiveEventId() && data.length > 0) {
          setActiveEventId(data[0].id);
          setActiveId(data[0].id);
        }
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar seus eventos."));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selecionar = (id: string) => {
    setActiveEventId(id);
    setActiveId(id);
    navigate("/organizador/evento");
  };

  const titulo = `${greeting()}, ${user ? firstName(user.nome) : "organizador"} 👋`;

  return (
    <>
      <PageHeader
        breadcrumb="Visão geral"
        title={titulo}
        actions={
          <button
            type="button"
            className={styles.cta}
            onClick={() => navigate("/organizador/eventos/novo")}
          >
            + Novo evento
          </button>
        }
      />

      <div className={styles.body}>
        <section className={styles.tableCard}>
          <div className={styles.tableHead}>
            <h3 className={styles.cardTitle}>Meus eventos</h3>
          </div>

          {error && <div className={styles.empty}>{error}</div>}
          {!error && eventos === null && (
            <div className={styles.empty}>Carregando seus eventos…</div>
          )}
          {!error && eventos?.length === 0 && (
            <div className={styles.empty}>
              Você ainda não criou nenhum evento.{" "}
              <button
                type="button"
                className={styles.inlineCta}
                onClick={() => navigate("/organizador/eventos/novo")}
              >
                Criar o primeiro
              </button>
              .
            </div>
          )}

          {eventos && eventos.length > 0 && (
            <div className={styles.eventGrid}>
              {eventos.map((ev) => {
                const ativo = ev.id === activeId;
                return (
                  <button
                    type="button"
                    key={ev.id}
                    className={styles.eventCard}
                    data-active={ativo ? "1" : undefined}
                    onClick={() => selecionar(ev.id)}
                  >
                    <div
                      className={styles.eventCover}
                      style={{ background: gradientFor(ev.id) }}
                    />
                    <div className={styles.eventBody}>
                      <div className={styles.eventTopRow}>
                        <div className={styles.eventTitle}>{ev.nome}</div>
                        <StatusPill status={ev.status} />
                      </div>
                      <div className={styles.eventMeta}>
                        📅 {dateLong(ev.data_inicio)}
                      </div>
                      <div className={styles.eventMeta}>📍 {ev.local}</div>
                      {ativo && (
                        <div className={styles.eventActiveTag}>Evento ativo</div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <section className={styles.tableCard}>
          <div className={styles.tableHead}>
            <h3 className={styles.cardTitle}>Métricas e financeiro</h3>
          </div>
          <div className={styles.empty}>
            UC14 (Relatório Financeiro) ainda não foi implementado no backend.
            Quando disponível, métricas de receita, ticket médio e gráfico de
            vendas aparecerão aqui.
          </div>
        </section>
      </div>
    </>
  );
};
