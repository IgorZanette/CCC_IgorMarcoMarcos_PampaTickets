import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { gradientFor, listarEventos, type Evento } from "../../api/eventos";
import { EventCard } from "../../components/EventCard";
import { Icon } from "../../components/Icon";
import { Skeleton } from "../../components/Skeleton";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong } from "../../lib/format";

import styles from "./HomePage.module.css";

export const HomePage = () => {
  const [events, setEvents] = useState<Evento[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listarEventos()
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar eventos."));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <section className={styles.heroSection}>
        <div className={styles.empty}>{error}</div>
      </section>
    );
  }

  if (events === null) {
    return (
      <section className={styles.heroSection}>
        <Skeleton height={280} radius="var(--pt-r-2xl)" />
      </section>
    );
  }

  if (events.length === 0) {
    return (
      <section className={styles.heroSection}>
        <div className={styles.empty}>
          Nenhum evento publicado por enquanto. Volte em breve!
        </div>
      </section>
    );
  }

  const featured = events[0];
  const trending = events.slice(0, 4);
  const week = events.slice(4, 8);

  return (
    <>
      <section className={styles.heroSection}>
        <Link
          to={`/eventos/${featured.id}`}
          className={styles.hero}
          style={{ background: gradientFor(featured.id) }}
        >
          <div className={styles.heroOverlay} />
          <div className={styles.heroContent}>
            <span className={styles.heroEyebrow}>
              <Icon name="bolt" /> Em destaque
            </span>
            <h1 className={styles.heroTitle}>{featured.nome}</h1>
            <div className={styles.heroMeta}>
              <span>
                <Icon name="calendar" /> {dateLong(featured.data_inicio)}
              </span>
              <span>
                <Icon name="pin" /> {featured.local}
              </span>
            </div>
            <div className={styles.heroActions}>
              <span className={styles.heroPrimary}>Comprar ingressos →</span>
              <span className={styles.heroSecondary}>Mais informações</span>
            </div>
          </div>
        </Link>
      </section>

      <Carousel
        title={
          <>
            <Icon name="flame" /> Em alta agora
          </>
        }
        subtitle="Os destaques desta semana"
        events={trending}
      />

      {week.length > 0 && (
        <Carousel
          title={
            <>
              <Icon name="calendar" /> Esta semana
            </>
          }
          subtitle="Não perca o que vem aí"
          events={week}
        />
      )}
    </>
  );
};

const Carousel = ({
  title,
  subtitle,
  events,
}: {
  title: ReactNode;
  subtitle: string;
  events: Evento[];
}) => (
  <section className={styles.carouselSection}>
    <div className={styles.sectionHead}>
      <div>
        <h2 className={styles.sectionTitle}>{title}</h2>
        <div className={styles.sectionSub}>{subtitle}</div>
      </div>
      <Link to="/eventos" className={styles.sectionLink}>
        Ver todos →
      </Link>
    </div>
    <div className={styles.carousel}>
      {events.slice(0, 4).map((e) => (
        <EventCard key={e.id} ev={e} />
      ))}
    </div>
  </section>
);
