import styles from "./Spinner.module.css";

type SpinnerProps = {
  /** Diâmetro em px. Padrão: 40. */
  size?: number;
  /** Rótulo acessível para leitores de tela. */
  label?: string;
};

/**
 * Loader próprio do PampaTickets: um anel verde-pampa girando com o raio
 * dourado da marca piscando no centro, como um relâmpago — dá uma quebrada
 * de gelo na espera do usuário.
 */
export const Spinner = ({ size = 40, label = "Carregando…" }: SpinnerProps) => (
  <span
    className={styles.wrap}
    style={{ width: size, height: size }}
    role="status"
    aria-label={label}
  >
    <svg className={styles.ring} viewBox="0 0 24 24" aria-hidden="true">
      <circle className={styles.track} cx="12" cy="12" r="9" />
      <circle className={styles.arc} cx="12" cy="12" r="9" />
    </svg>
    <svg className={styles.bolt} viewBox="-1 -1.15 2 2.3" aria-hidden="true">
      <path
        d="M0.18 -1L-0.62 0.16L-0.04 0.16L-0.18 1L0.62 -0.16L0.04 -0.16Z"
        style={{ fill: "var(--pt-accent-hot)" }}
      />
    </svg>
  </span>
);

/** Bloco de espera centralizado: spinner + mensagem. */
export const LoadingBlock = ({
  message = "Carregando…",
  size = 40,
}: {
  message?: string;
  size?: number;
}) => (
  <div className={styles.block}>
    <Spinner size={size} label={message} />
    <span>{message}</span>
  </div>
);
