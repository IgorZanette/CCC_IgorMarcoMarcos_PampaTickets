import { Link } from "react-router-dom";

import { Logo } from "../components/Logo";
import styles from "./LandingPage.module.css";

export const LandingPage = () => (
  <div className={styles.page} data-theme="dark">
    <header className={styles.header}>
      <Logo size={32} />
      <nav className={styles.nav}>
        <Link to="/login" className={styles.navLink}>
          Entrar
        </Link>
        <Link to="/cadastro" className={styles.cta}>
          Criar conta
        </Link>
      </nav>
    </header>

    <section className={styles.hero}>
      <span className={styles.eyebrow}>⚡ PampaTickets · CCC · UPF</span>
      <h1 className={styles.title}>
        Os eventos do <em>pampa gaúcho</em>,
        <br />
        em um só lugar.
      </h1>
      <p className={styles.lead}>
        Descubra festivais, shows e clássicos no Rio Grande do Sul. Compre
        ingressos com PIX, boleto ou cartão e gerencie seus eventos como um
        verdadeiro produtor.
      </p>

      <div className={styles.actions}>
        <Link to="/inicio" className={styles.primary}>
          Sou participante →
        </Link>
        <Link to="/organizador" className={styles.secondary}>
          Sou organizador →
        </Link>
      </div>

      <div className={styles.demo}>
        <div className={styles.demoLine}>
          <span className={styles.demoDot} /> Demo navegável — sem login,
          consumindo dados de exemplo. As rotas com API caem para mocks quando o
          backend não está rodando.
        </div>
      </div>
    </section>

    <footer className={styles.footer}>
      <span>Projeto acadêmico · Universidade de Passo Fundo</span>
      <span className="pt-mono">v0.1.0</span>
    </footer>
  </div>
);
