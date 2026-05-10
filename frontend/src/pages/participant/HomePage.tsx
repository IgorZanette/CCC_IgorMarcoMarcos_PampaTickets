import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listarEventos } from "../../api/eventos";
import { EventCard } from "../../components/EventCard";
import { PT_CATEGORIES, type EventoSample } from "../../data/sample";
import { dateFull, dateLong, moneyShort } from "../../lib/format";

import styles from "./HomePage.module.css";

export const HomePage = () => {
  const [events, setEvents] = useState<EventoSample[]>([]);

  useEffect(() => {
    listarEventos().then(setEvents);
  }, []);

  if (events.length === 0) return null;

  const featured = events[0];
  const trending = events.slice(0, 4);
  const week = [events[2], events[4], events[1], events[3]].filter(
    (e): e is EventoSample => e !== undefined,
  );
  const ending = events.filter((e) => e.urgente || e.vendidos > 0.85).slice(0, 4);

  return (
    <>
      <section className={styles.heroSection}>
        <Link
          to={`/app/eventos/${featured.id}`}
          className={styles.hero}
          style={{ background: featured.img }}
        >
          <div className={styles.heroOverlay} />
          <div className={styles.heroContent}>
            <span className={styles.heroEyebrow}>⚡ Em destaque</span>
            <h1 className={styles.heroTitle}>{featured.nome}</h1>
            <div className={styles.heroMeta}>
              <span>📅 {dateLong(featured.data)}</span>
              <span>
                📍 {featured.local}, {featured.cidade}
              </span>
            </div>
            <div className={styles.heroActions}>
              <span className={styles.heroPrimary}>Comprar ingressos →</span>
              <span className={styles.heroSecondary}>Mais informações</span>
            </div>
          </div>
          <div className={styles.heroDots}>
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className={i === 0 ? styles.heroDotActive : styles.heroDot}
              />
            ))}
          </div>
        </Link>
      </section>

      <section className={styles.categoriesSection}>
        <div className={styles.categories}>
          {PT_CATEGORIES.map((c) => (
            <Link
              to={`/app/explorar?cat=${c.id}`}
              key={c.id}
              className={styles.category}
            >
              <span className={styles.categoryIcon}>{c.icon}</span>
              <span className={styles.categoryLabel}>{c.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <Carousel
        title="🔥 Em alta agora"
        subtitle="Os mais vendidos da semana"
        events={trending}
      />

      <Carousel
        title="📅 Esta semana"
        subtitle="Não perca o que vem aí"
        events={week}
      />

      {ending.length > 0 && (
        <section className={styles.endingSection}>
          <div className={styles.sectionHead}>
            <div>
              <h2 className={styles.sectionTitle}>⏰ Últimos ingressos</h2>
              <div className={styles.sectionSub}>Esses não vão durar muito</div>
            </div>
            <Link to="/app/explorar" className={styles.sectionLink}>
              Ver todos →
            </Link>
          </div>
          <div className={styles.endingGrid}>
            {ending.map((e) => (
              <EndingRow key={e.id} ev={e} />
            ))}
          </div>
        </section>
      )}
    </>
  );
};

const Carousel = ({
  title,
  subtitle,
  events,
}: {
  title: string;
  subtitle: string;
  events: EventoSample[];
}) => (
  <section className={styles.carouselSection}>
    <div className={styles.sectionHead}>
      <div>
        <h2 className={styles.sectionTitle}>{title}</h2>
        <div className={styles.sectionSub}>{subtitle}</div>
      </div>
      <div className={styles.scrollControls}>
        <button className={styles.scrollBtn} aria-label="Anterior">
          ‹
        </button>
        <button className={styles.scrollBtn} aria-label="Próximo">
          ›
        </button>
      </div>
    </div>
    <div className={styles.carousel}>
      {events.slice(0, 4).map((e) => (
        <EventCard key={e.id} ev={e} />
      ))}
    </div>
  </section>
);

const EndingRow = ({ ev }: { ev: EventoSample }) => {
  const d = dateFull(ev.data);
  const lote = ev.lotes.find((l) => l.restantes > 0);
  return (
    <Link to={`/app/eventos/${ev.id}`} className={styles.endingRow}>
      <div className={styles.endingCover} style={{ background: ev.img }} />
      <div className={styles.endingInfo}>
        <div className={styles.endingTitle}>{ev.nome}</div>
        <div className={styles.endingMeta}>
          {d.dia}/{d.mes} · {ev.cidade}
        </div>
        {lote && (
          <div className={styles.endingWarn}>
            ⚠ Restam {lote.restantes} ingressos
          </div>
        )}
      </div>
      <div className={styles.endingPrice}>
        <div className={styles.endingPriceValue}>{moneyShort(ev.precoMin)}</div>
        <div className={styles.endingPriceLabel}>a partir de</div>
      </div>
    </Link>
  );
};
