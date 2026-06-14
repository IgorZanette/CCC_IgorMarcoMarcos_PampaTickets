import { NavLink, Outlet, useLocation, useMatch, useNavigate } from "react-router-dom";

import { logout } from "../api/auth";
import { type Evento } from "../api/eventos";
import { Logo } from "../components/Logo";
import { PageTransition } from "../components/PageTransition";
import { StatusPill } from "../components/StatusPill";
import { useEvento } from "../lib/active-event";
import { initials, useCurrentUser } from "../lib/auth-store";
import styles from "./OrganizerLayout.module.css";

// Contexto repassado às páginas filhas via <Outlet context>. As páginas de evento
// leem o id da rota (useParams) e podem reusar o evento já hidratado aqui.
export type OrgOutlet = {
  evento: Evento | null;
  loading: boolean;
  error: boolean;
};

const eventNavItems = (id: string) => [
  { to: `/organizador/eventos/${id}`, label: "Visão geral", icon: "★", end: true },
  { to: `/organizador/eventos/${id}/lotes`, label: "Lotes & vendas", icon: "◐" },
  { to: `/organizador/eventos/${id}/cupons`, label: "Cupons", icon: "◇" },
  { to: `/organizador/eventos/${id}/cortesias`, label: "Cortesias", icon: "✦" },
  { to: `/organizador/eventos/${id}/checkin`, label: "Check-in ao vivo", icon: "✓" },
  { to: `/organizador/eventos/${id}/participantes`, label: "Participantes", icon: "👥" },
  { to: `/organizador/eventos/${id}/financeiro`, label: "Financeiro", icon: "$" },
];

export const OrganizerLayout = () => {
  const user = useCurrentUser();
  const navigate = useNavigate();
  const location = useLocation();

  // O id do evento ativo vem da URL (não de localStorage). useParams no layout-pai
  // não enxerga o :id das rotas filhas; useMatch enxerga.
  const match = useMatch("/organizador/eventos/:id/*");
  const activeId = match?.params.id ?? null;
  const { evento, loading, error } = useEvento(activeId);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className={styles.shell} data-theme="light">
      <aside className={styles.sidebar}>
        <div className={styles.brand} data-theme="dark">
          <Logo size={28} />
          <span className={styles.brandRole}>ORGANIZADOR</span>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionLabel}>Painel</div>
          <NavLink
            to="/organizador"
            end
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
            }
          >
            <span className={styles.navIcon}>☰</span>
            Eventos
          </NavLink>
        </div>

        {activeId && (
          <div className={styles.section}>
            <NavLink to="/organizador" className={styles.backLink}>
              ← Todos os eventos
            </NavLink>
            <div className={styles.eventHead}>
              <span className={styles.eventName}>{evento?.nome ?? "Evento"}</span>
              {evento && <StatusPill status={evento.status} />}
            </div>
            {eventNavItems(activeId).map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
                }
              >
                <span className={styles.navIcon}>{n.icon}</span>
                {n.label}
              </NavLink>
            ))}
          </div>
        )}

        <div className={styles.userCard}>
          <div className={styles.userAvatar}>{user ? initials(user.nome) : ""}</div>
          <div className={styles.userInfo}>
            <div className={styles.userName}>{user?.nome ?? "Convidado"}</div>
            <div className={styles.userEmail}>
              {user?.email ?? "Faça login para gerenciar"}
            </div>
          </div>
          {user && (
            <button
              type="button"
              className={styles.userLogout}
              onClick={handleLogout}
              aria-label="Sair"
              title="Sair"
            >
              ⏻
            </button>
          )}
        </div>
      </aside>

      <main className={styles.main}>
        <PageTransition key={location.pathname}>
          <Outlet context={{ evento, loading, error } satisfies OrgOutlet} />
        </PageTransition>
      </main>
    </div>
  );
};
