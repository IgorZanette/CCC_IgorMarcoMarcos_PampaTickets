import type { ReactNode } from "react";

import { Icon } from "./Icon";
import styles from "./EmptyState.module.css";

type EmptyStateProps = {
  icon?: ReactNode;
  title: string;
  hint?: string;
  action?: ReactNode;
};

// Estado vazio com ícone + título + dica e CTA opcional — substitui os
// "Nenhum…" de texto puro nas listagens, deixando o vazio mais acolhedor.
export const EmptyState = ({
  icon = <Icon name="sparkle" />,
  title,
  hint,
  action,
}: EmptyStateProps) => (
  <div className={styles.wrap}>
    <div className={styles.icon} aria-hidden>
      {icon}
    </div>
    <div className={styles.title}>{title}</div>
    {hint && <div className={styles.hint}>{hint}</div>}
    {action && <div className={styles.cta}>{action}</div>}
  </div>
);
