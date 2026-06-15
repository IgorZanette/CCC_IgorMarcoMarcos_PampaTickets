import { Link } from "react-router-dom";

import { Icon, type IconName } from "../components/Icon";
import { Logo } from "../components/Logo";
import { PampaBackdrop } from "../components/PampaBackdrop";
import styles from "./LandingPage.module.css";

type Feature = {
  icon: IconName;
  title: string;
  desc: string;
};

const featuresParticipante: Feature[] = [
  {
    icon: "search",
    title: "Vitrine e busca de eventos",
    desc: "Explore festivais, shows e clássicos do RS com busca por nome, cidade e data.",
  },
  {
    icon: "ticket",
    title: "Compra de ingressos",
    desc: "Escolha o lote, aplique cupom de desconto e finalize a compra em poucos cliques.",
  },
  {
    icon: "card",
    title: "Pagamento flexível",
    desc: "Pague com PIX, boleto ou cartão de crédito — processado com segurança via Asaas.",
  },
  {
    icon: "mailQr",
    title: "Ingresso por e-mail",
    desc: "Receba o ingresso em PDF com o QR Code já no corpo do e-mail, pronto para escanear.",
  },
  {
    icon: "tickets",
    title: "Meus ingressos",
    desc: "Acesse todos os seus ingressos e QR Codes pelo site a qualquer momento.",
  },
  {
    icon: "refund",
    title: "Reembolso",
    desc: "Solicite reembolso quando aplicável e acompanhe o estorno até a conclusão.",
  },
  {
    icon: "certificate",
    title: "Certificado de participação",
    desc: "Após o check-in, baixe o certificado em PDF comprovando sua presença no evento.",
  },
  {
    icon: "photo",
    title: "Galeria de fotos",
    desc: "Reviva o evento pela galeria de fotos publicada pelo organizador.",
  },
];

const featuresOrganizador: Feature[] = [
  {
    icon: "calendar",
    title: "Gestão de eventos",
    desc: "Crie, publique e cancele eventos com dupla confirmação nas transições críticas.",
  },
  {
    icon: "layers",
    title: "Lotes de ingressos",
    desc: "Defina lotes com preço, quantidade e disponibilidade, controlando a venda em tempo real.",
  },
  {
    icon: "coupon",
    title: "Cupons de desconto",
    desc: "Crie cupons percentuais ou de valor fixo para impulsionar as vendas.",
  },
  {
    icon: "gift",
    title: "Cortesias",
    desc: "Emita ingressos gratuitos para convidados — entregues automaticamente por e-mail.",
  },
  {
    icon: "qr",
    title: "Check-in por QR Code",
    desc: "Valide ingressos na portaria escaneando o QR Code, com proteção contra reuso.",
  },
  {
    icon: "people",
    title: "Lista de participantes",
    desc: "Acompanhe quem comprou e quem já fez check-in em cada evento.",
  },
  {
    icon: "chart",
    title: "Relatório financeiro",
    desc: "Visualize receita, vendas por lote e reembolsos em um painel consolidado.",
  },
  {
    icon: "photo",
    title: "Galeria do evento",
    desc: "Publique as fotos do evento para que os participantes revivam o momento.",
  },
];

const techBand: { icon: IconName; label: string }[] = [
  { icon: "shield", label: "Login seguro com JWT" },
  { icon: "mailCheck", label: "Confirmação de e-mail" },
  { icon: "card", label: "Pagamentos via Asaas" },
  { icon: "qr", label: "QR Code em todo ingresso" },
  { icon: "chat", label: "Notificações WhatsApp" },
];

const FeatureCard = ({ icon, title, desc }: Feature) => (
  <div className={styles.featureCard}>
    <span className={styles.featureIcon}>
      <Icon name={icon} spark />
    </span>
    <h3 className={styles.featureTitle}>{title}</h3>
    <p className={styles.featureDesc}>{desc}</p>
  </div>
);

export const LandingPage = () => (
  <div className={styles.page} data-theme="dark">
    <div className={styles.pampaBackdrop} aria-hidden="true">
      <PampaBackdrop />
    </div>

    <header className={styles.header}>
      <Logo size={32} />
      <nav className={styles.nav}>
        <a href="#funcionalidades" className={styles.navLink}>
          Funcionalidades
        </a>
        <Link to="/login" className={styles.navLink}>
          Entrar
        </Link>
        <Link to="/cadastro" className={styles.cta}>
          Criar conta
        </Link>
      </nav>
    </header>

    <section className={styles.hero}>
      <span className={styles.eyebrow}>
        <Icon name="bolt" style={{ color: "var(--pt-accent-hot)" }} /> PampaTickets
        · CCC · UPF
      </span>
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
        <Link
          to="/cadastro"
          state={{ perfil: "PARTICIPANTE" }}
          className={styles.primary}
        >
          Sou participante →
        </Link>
        <Link
          to="/cadastro"
          state={{ perfil: "ORGANIZADOR" }}
          className={styles.secondary}
        >
          Sou organizador →
        </Link>
      </div>

      <a href="#funcionalidades" className={styles.scrollHint}>
        Conheça as funcionalidades ↓
      </a>
    </section>

    <section id="funcionalidades" className={styles.features}>
      <div className={styles.featuresHead}>
        <span className={styles.eyebrow}>Tudo o que a plataforma faz</span>
        <h2 className={styles.featuresTitle}>
          Uma plataforma completa, da venda ao certificado.
        </h2>
        <p className={styles.featuresLead}>
          Do primeiro clique do participante ao relatório financeiro do
          organizador — todas as funcionalidades do PampaTickets.
        </p>
      </div>

      <div className={styles.personaBlock}>
        <div className={styles.personaHeader}>
          <span className={styles.personaTag}>Para participantes</span>
          <p className={styles.personaSub}>
            Quem vai curtir o evento — da descoberta ao certificado.
          </p>
        </div>
        <div className={styles.featureGrid}>
          {featuresParticipante.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </div>

      <div className={styles.personaBlock}>
        <div className={styles.personaHeader}>
          <span className={`${styles.personaTag} ${styles.personaTagGold}`}>
            Para organizadores
          </span>
          <p className={styles.personaSub}>
            Quem produz o evento — controle total da operação.
          </p>
        </div>
        <div className={styles.featureGrid}>
          {featuresOrganizador.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </div>

      <div className={styles.techBand}>
        {techBand.map(({ icon, label }) => (
          <span key={label} className={styles.techItem}>
            <Icon name={icon} />
            {label}
          </span>
        ))}
      </div>
    </section>

    <footer className={styles.footer}>
      <span>Projeto acadêmico · Universidade de Passo Fundo</span>
      <span className="pt-mono">v0.1.0</span>
    </footer>
  </div>
);
