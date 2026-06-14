import type { ReactNode } from "react";

import styles from "./MetricCard.module.css";

type Props = {
  label: string;
  value: ReactNode;
  delta?: number;
  sub?: string;
  tone?: "ok" | "warn" | "danger" | "neutral";
};

export const MetricCard = ({ label, value, delta, sub, tone }: Props) => (
  <div className={styles.card} data-tone={tone}>
    <div className={styles.label}>{label}</div>
    <div className={styles.value} data-tone={tone}>
      {value}
    </div>
    {(delta !== undefined || sub) && (
      <div className={styles.footer}>
        {delta !== undefined && (
          <span
            className={styles.delta}
            data-tone={delta >= 0 ? "ok" : "danger"}
          >
            {delta >= 0 ? "↑" : "↓"} {Math.abs(delta * 100).toFixed(1)}%
          </span>
        )}
        {sub && <span className={styles.sub}>{sub}</span>}
      </div>
    )}
  </div>
);
