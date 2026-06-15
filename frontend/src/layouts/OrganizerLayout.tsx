import { NavLink, Outlet, useLocation, useMatch, useNavigate } from "react-router-dom";

import { logout } from "../api/auth";
import { type Evento } from "../api/eventos";
import { Icon, type IconName } from "../components/Icon";
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

const eventNavItems = (
  id: string,
): { to: string; label: string; icon: IconName; end?: boolean }[] => [
  { to: `/organizador/eventos/${id}`, label: "Visão geral", icon: "grid", end: true },
  { to: `/organizador/eventos/${id}/lotes`, label: "Lotes & vendas", icon: "layers" },
  { to: `/organizador/eventos/${id}/cupons`, label: "Cupons", icon: "coupon" },
  { to: `/organizador/eventos/${id}/cortesias`, label: "Cortesias", icon: "gift" },
  { to: `/organizador/eventos/${id}/fotos`, label: "Galeria", icon: "photo" },
  { to: `/organizador/eventos/${id}/checkin`, label: "Check-in ao vivo", icon: "qr" },
  { to: `/organizador/eventos/${id}/participantes`, label: "Participantes", icon: "people" },
  { to: `/organizador/eventos/${id}/financeiro`, label: "Financeiro", icon: "chart" },
];

export const OrganizerLayout = () => {
  const user = useCurrentUser();
  const navigate = useNavigate();
  const location = useLocation();

  // O id do evento ativo vem da URL (não de localStorage). useParams no layout-pai
  // não enxerga o :id das rotas filhas; useMatch enxerga.
  const match = useMatch("/organizador/eventos/:id/*");
  // "novo" é o segmento reservado da tela de criação — não é um id de evento.
  // Tratá-lo como id faria o layout buscar GET /eventos/novo (erro de UUID no
  // backend) e exibir a navegação de lotes/cupons antes do evento existir.
  const rawId = match?.params.id ?? null;
  const activeId = rawId === "novo" ? null : rawId;
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
            <span className={styles.navIcon}>
              <Icon name="calendar" />
            </span>
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
                <span className={styles.navIcon}>
                  <Icon name={n.icon} />
                </span>
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
              <Icon name="power" />
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
