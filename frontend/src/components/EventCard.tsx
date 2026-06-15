import { Link } from "react-router-dom";

import { gradientFor, type Evento } from "../api/eventos";
import { dateFull } from "../lib/format";
import { Icon } from "./Icon";
import styles from "./EventCard.module.css";

type Props = {
  ev: Evento;
  to?: string;
};

export const EventCard = ({ ev, to }: Props) => {
  const d = dateFull(ev.data_inicio);
  const href = to ?? `/eventos/${ev.id}`;
  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cover} style={{ background: gradientFor(ev.id) }} />
      <div className={styles.body}>
        <div className={styles.dateBlock}>
          <div className={styles.mes}>{d.mes}</div>
          <div className={styles.dia}>{d.dia}</div>
          <div className={styles.semana}>{d.semana}</div>
        </div>
        <div className={styles.info}>
          <div className={styles.title}>{ev.nome}</div>
          <div className={styles.meta}>
            <Icon name="pin" /> {ev.local}
          </div>
        </div>
      </div>
    </Link>
  );
};
