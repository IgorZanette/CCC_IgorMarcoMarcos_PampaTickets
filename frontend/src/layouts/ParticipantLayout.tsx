import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { Icon } from "../components/Icon";
import { Logo } from "../components/Logo";
import { PageTransition } from "../components/PageTransition";
import { firstName, initials, useCurrentUser } from "../lib/auth-store";
import styles from "./ParticipantLayout.module.css";

const NAV = [
  { to: "/inicio", label: "Início", end: true },
  { to: "/eventos", label: "Explorar", end: false },
  { to: "/meus-ingressos", label: "Meus ingressos", end: false },
];

export const ParticipantLayout = () => {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const user = useCurrentUser();

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/eventos${search ? `?q=${encodeURIComponent(search)}` : ""}`);
  };

  return (
    <div className={styles.shell} data-theme="dark">
      <header className={styles.topbar}>
        <div className={styles.bar}>
          <Link to="/inicio" className={styles.brand} aria-label="Ir para início">
            <Logo />
          </Link>

          <nav className={styles.nav}>
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>

          <form className={styles.searchWrap} onSubmit={submitSearch}>
            <span className={styles.searchIcon} aria-hidden>
              <Icon name="search" />
            </span>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onFocus={() => {
                if (location.pathname !== "/eventos") navigate("/eventos");
              }}
              placeholder="Buscar evento, artista, local…"
              className={styles.search}
              aria-label="Buscar eventos"
            />
          </form>

          {user ? (
            <Link to="/meus-ingressos" className={styles.avatar}>
              <span className={styles.avatarMark}>{initials(user.nome)}</span>
              <span className={styles.avatarName}>{firstName(user.nome)}</span>
            </Link>
          ) : (
            <Link to="/login" className={styles.avatar}>
              <span className={styles.avatarName}>Entrar</span>
            </Link>
          )}
        </div>
      </header>

      <main className={styles.main}>
        <PageTransition key={location.pathname}>
          <Outlet />
        </PageTransition>
      </main>
    </div>
  );
};
