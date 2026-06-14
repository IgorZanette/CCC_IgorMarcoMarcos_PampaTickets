import styles from "./StatusPill.module.css";

type Status =
  | "PAGO"
  | "PENDENTE"
  | "CANCELADO"
  | "CONFIRMADO"
  | "PASSADO"
  | "PUBLICADO"
  | "CHECK-IN"
  | "ESGOTADO"
  | "VENDENDO"
  | "AO VIVO";

type Props = {
  status: Status | string;
  pulse?: boolean;
};

const TONE: Record<string, string> = {
  PAGO: "ok",
  CONFIRMADO: "ok",
  PUBLICADO: "ok",
  "CHECK-IN": "ok",
  VENDENDO: "ok",
  "AO VIVO": "ok",
  ATIVO: "ok",
  PRESENTE: "ok",
  PENDENTE: "warn",
  RASCUNHO: "warn",
  PASSADO: "neutral",
  ENCERRADO: "neutral",
  REEMBOLSADO: "neutral",
  UTILIZADO: "neutral",
  CANCELADO: "danger",
  ESGOTADO: "danger",
};

export const StatusPill = ({ status, pulse }: Props) => {
  const tone = TONE[status] ?? "neutral";
  return (
    <span className={styles.pill} data-tone={tone}>
      <span className={styles.dot} data-pulse={pulse ? "1" : undefined} />
      {status}
    </span>
  );
};
