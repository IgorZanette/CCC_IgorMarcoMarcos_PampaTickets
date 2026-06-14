import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  gradientFor,
  listarEventosOrganizador,
  type Evento,
} from "../../api/eventos";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { SkeletonGrid } from "../../components/Skeleton";
import { StatusPill } from "../../components/StatusPill";
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

  useEffect(() => {
    let cancelled = false;
    listarEventosOrganizador()
      .then((data) => {
        if (!cancelled) setEventos(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar seus eventos."));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const abrir = (id: string) => navigate(`/organizador/eventos/${id}`);

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
            <div className={styles.eventGrid}>
              <SkeletonGrid count={3} />
            </div>
          )}
          {!error && eventos?.length === 0 && (
            <EmptyState
              icon="🎪"
              title="Você ainda não criou nenhum evento"
              hint="Publique seu primeiro evento e comece a vender ingressos em minutos."
              action={
                <button
                  type="button"
                  className={styles.cta}
                  onClick={() => navigate("/organizador/eventos/novo")}
                >
                  + Criar meu primeiro evento
                </button>
              }
            />
          )}

          {eventos && eventos.length > 0 && (
            <div className={styles.eventGrid}>
              {eventos.map((ev) => (
                <button
                  type="button"
                  key={ev.id}
                  className={styles.eventCard}
                  onClick={() => abrir(ev.id)}
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
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
};
