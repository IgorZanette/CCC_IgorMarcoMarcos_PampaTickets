import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { logout } from "../api/auth";
import { initials, useCurrentUser } from "../lib/auth-store";
import styles from "./OrganizerLayout.module.css";

const TOP_NAV = [
  { to: "/organizador", label: "Visão geral", icon: "◫", end: true },
  { to: "/organizador/financeiro", label: "Financeiro", icon: "$" },
];

const TOP_NAV_DISABLED = [
  { label: "Eventos", icon: "☰" },
  { label: "Cupons", icon: "◇" },
  { label: "Cortesias", icon: "✦" },
  { label: "Relatórios", icon: "📊" },
];

const EVENT_NAV = [
  { to: "/organizador/evento", label: "Detalhes do evento", icon: "★" },
  { to: "/organizador/lotes", label: "Lotes & vendas", icon: "◐" },
  { to: "/organizador/checkin", label: "Check-in ao vivo", icon: "✓" },
  { to: "/organizador/participantes", label: "Participantes", icon: "👥" },
];

export const OrganizerLayout = () => {
  const user = useCurrentUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
  <div className={styles.shell} data-theme="light">
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.mark}>P</div>
        <div>
          <div className={styles.brandName}>PampaTickets</div>
          <div className={styles.brandRole}>ORGANIZADOR</div>
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>Painel</div>
        {TOP_NAV.map((n) => (
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
        {TOP_NAV_DISABLED.map((n) => (
          <span key={n.label} className={`${styles.navItem} ${styles.navDisabled}`}>
            <span className={styles.navIcon}>{n.icon}</span>
            {n.label}
          </span>
        ))}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>Festival de Inverno</div>
        {EVENT_NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
            }
          >
            <span className={styles.navIcon}>{n.icon}</span>
            {n.label}
          </NavLink>
        ))}
      </div>

      <div className={styles.userCard}>
        <div className={styles.userAvatar}>
          {user ? initials(user.nome) : ""}
        </div>
        <div className={styles.userInfo}>
          <div className={styles.userName}>
            {user?.nome ?? "Convidado"}
          </div>
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
      <Outlet />
    </main>
  </div>
  );
};
