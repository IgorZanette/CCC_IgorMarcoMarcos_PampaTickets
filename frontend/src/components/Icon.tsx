import type { CSSProperties, ReactNode } from "react";

/**
 * Set de ícones próprios do PampaTickets — substitui qualquer emoji/glifo
 * genérico no site, garantindo uma linguagem visual única e coesa.
 *
 * - pictograma em traço (`currentColor`) → herda a cor do contexto, então o
 *   mesmo ícone serve em verde, vermelho (erro), âmbar (aviso) etc.;
 * - assinatura da marca: a faísca dourada (o ⚡ do selo PampaTickets) entra
 *   apenas quando `spark` é passado — usada nos cards da landing. Ícones
 *   utilitários (check, aviso, pin…) ficam limpos para adaptar a cor.
 *
 * Tamanho padrão = 1em (acompanha o `font-size` do contexto). Passe `size`
 * para fixar em pixels.
 */

export type IconName =
  // marca / features
  | "search"
  | "ticket"
  | "tickets"
  | "card"
  | "mailQr"
  | "refund"
  | "certificate"
  | "photo"
  | "calendar"
  | "layers"
  | "coupon"
  | "gift"
  | "qr"
  | "people"
  | "chart"
  | "shield"
  | "mailCheck"
  | "chat"
  // utilitários
  | "pin"
  | "check"
  | "close"
  | "warning"
  | "hourglass"
  | "document"
  | "wave"
  | "celebrate"
  | "flame"
  | "lock"
  | "camera"
  | "eye"
  | "tent"
  | "external"
  | "sparkle"
  | "menu"
  | "power"
  | "grid"
  | "bolt";

type SparkPos = [x: number, y: number, s?: number];

type IconDef = {
  body: ReactNode;
  /** Posição da faísca dourada, quando o ícone aceita a assinatura da marca. */
  spark?: SparkPos;
};

/**
 * Faísca dourada — a assinatura da marca: um raiozinho (⚡), o mesmo do selo
 * PampaTickets. Desenhado num box normalizado [-1,1] e posicionado/escalado
 * por (x, y, s) para caber em qualquer ícone.
 */
const Spark = ({ x, y, s = 1.6 }: { x: number; y: number; s?: number }) => (
  <path
    transform={`translate(${x} ${y}) scale(${s})`}
    d="M0.18 -1L-0.62 0.16L-0.04 0.16L-0.18 1L0.62 -0.16L0.04 -0.16Z"
    style={{ fill: "var(--pt-accent-hot)" }}
    stroke="none"
  />
);

const fill = "currentColor";

const ICONS: Record<IconName, IconDef> = {
  // ── Marca / features ───────────────────────────────────────
  search: {
    body: (
      <>
        <circle cx="10.5" cy="10.5" r="6" />
        <line x1="14.9" y1="14.9" x2="20" y2="20" />
      </>
    ),
    spark: [10.5, 10.5, 2],
  },
  ticket: {
    body: (
      <>
        <path d="M4 7.5h16a1 1 0 0 1 1 1v2.1a1.7 1.7 0 0 0 0 3.4v2.1a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2.1a1.7 1.7 0 0 0 0-3.4V8.5a1 1 0 0 1 1-1z" />
        <line x1="14" y1="8" x2="14" y2="17" strokeDasharray="1.4 1.7" />
      </>
    ),
    spark: [8.4, 12.25, 1.7],
  },
  tickets: {
    body: (
      <>
        <path d="M6.5 8.5V7.2A1.5 1.5 0 0 1 8 5.7h11A1.5 1.5 0 0 1 20.5 7.2v8a1.5 1.5 0 0 1-1.5 1.5h-1.2" />
        <rect x="3.5" y="8.5" width="13" height="9" rx="1.6" />
      </>
    ),
    spark: [13.5, 13, 1.5],
  },
  card: {
    body: (
      <>
        <rect x="3" y="6" width="18" height="12" rx="2" />
        <line x1="3" y1="10" x2="21" y2="10" />
        <line x1="6.5" y1="14.5" x2="11" y2="14.5" />
      </>
    ),
    spark: [17.5, 14.3, 1.6],
  },
  mailQr: {
    body: (
      <>
        <rect x="3" y="5.5" width="18" height="13" rx="2" />
        <path d="M3.6 6.6 L12 12.4 L20.4 6.6" />
        <path
          d="M14.6 13.4h2.1v2.1h-2.1z M18 13.4h2.1v2.1H18z M14.6 16.8h2.1v2.1h-2.1z"
          fill={fill}
          stroke="none"
        />
      </>
    ),
    spark: [19, 17.9, 1.3],
  },
  refund: {
    body: (
      <>
        <path d="M5 12a7 7 0 1 0 2.5-5.4" />
        <path d="M4 4.2 L4.5 8.4 L8.7 7.9" />
      </>
    ),
    spark: [12, 12, 1.9],
  },
  certificate: {
    body: (
      <>
        <circle cx="12" cy="9.5" r="5" />
        <path d="M9 13.7 L7.6 20.5 L12 18 L16.4 20.5 L15 13.7" />
      </>
    ),
    spark: [12, 9.5, 2],
  },
  photo: {
    body: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M4 17.5 L9 12 L12.5 15 L16 11 L20 16" />
      </>
    ),
    spark: [8, 9, 1.7],
  },
  calendar: {
    body: (
      <>
        <rect x="3.5" y="5" width="17" height="15" rx="2" />
        <line x1="3.5" y1="9.5" x2="20.5" y2="9.5" />
        <line x1="8" y1="3.3" x2="8" y2="6.4" />
        <line x1="16" y1="3.3" x2="16" y2="6.4" />
      </>
    ),
    spark: [12, 14.5, 1.8],
  },
  layers: {
    body: (
      <>
        <path d="M12 4 L20.5 8.4 L12 12.8 L3.5 8.4 Z" />
        <path d="M4 11.8 L12 16 L20 11.8" />
        <path d="M4 15.2 L12 19.4 L20 15.2" />
      </>
    ),
    spark: [20, 5.6, 1.4],
  },
  coupon: {
    body: (
      <>
        <path d="M12.5 3.6 H20.4 V11.5 L11.5 20.4 a1.5 1.5 0 0 1-2.1 0 L3.6 14.6 a1.5 1.5 0 0 1 0-2.1 Z" />
        <line x1="8.6" y1="15.4" x2="13.4" y2="10.6" />
        <circle cx="9.4" cy="11.4" r="0.7" fill={fill} stroke="none" />
        <circle cx="12.6" cy="14.6" r="0.7" fill={fill} stroke="none" />
      </>
    ),
    spark: [16.8, 7.2, 1.4],
  },
  gift: {
    body: (
      <>
        <rect x="4.2" y="9.6" width="15.6" height="9.4" rx="1.4" />
        <rect x="3.2" y="6.4" width="17.6" height="3.4" rx="0.9" />
        <line x1="12" y1="9.8" x2="12" y2="19" />
        <path d="M12 6.4 C10 3.2 6.6 4.6 8.6 6.4 M12 6.4 C14 3.2 17.4 4.6 15.4 6.4" />
      </>
    ),
    spark: [12, 5, 1.3],
  },
  qr: {
    body: (
      <>
        <rect x="4" y="4" width="6.5" height="6.5" rx="1.2" />
        <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.2" />
        <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.2" />
        <path
          d="M13.5 13.5h2.4v2.4h-2.4z M17.6 13.5H20v2.4h-2.4z M13.5 17.6h2.4V20h-2.4z"
          fill={fill}
          stroke="none"
        />
      </>
    ),
    spark: [18.6, 18.6, 1.3],
  },
  people: {
    body: (
      <>
        <circle cx="9" cy="8.5" r="3.2" />
        <path d="M3.4 19.2 a5.6 5.6 0 0 1 11.2 0" />
        <path d="M15.6 5.8 a3.1 3.1 0 0 1 0 5.6" />
        <path d="M16.4 13.4 a5.6 5.6 0 0 1 4.2 5.8" />
      </>
    ),
    spark: [19.5, 6.5, 1.3],
  },
  chart: {
    body: (
      <>
        <path d="M4 4 V19.5 a0.5 0.5 0 0 0 0.5 0.5 H20" />
        <path d="M8 20 V14" />
        <path d="M12.5 20 V10.5" />
        <path d="M17 20 V7" />
      </>
    ),
    spark: [17, 4.5, 1.5],
  },
  shield: {
    body: (
      <>
        <path d="M12 3 L19 5.8 V11 C19 15.8 16 18.8 12 20.8 C8 18.8 5 15.8 5 11 V5.8 Z" />
        <path d="M9.2 11.6 L11.2 13.6 L15 9.6" />
      </>
    ),
    spark: [17.3, 5.6, 1.2],
  },
  mailCheck: {
    body: (
      <>
        <path d="M3 7.5 a2 2 0 0 1 2-2 h14 a2 2 0 0 1 2 2 v6.5 a2 2 0 0 1-2 2 H10.5" />
        <path d="M3.6 7 L12 12.6 L20.4 7" />
        <path d="M3.8 17.4 L6.1 19.7 L10.1 15.7" />
      </>
    ),
    spark: [18.2, 4.9, 1.2],
  },
  chat: {
    body: (
      <path d="M4 17.5 V8 A3 3 0 0 1 7 5 h10 a3 3 0 0 1 3 3 v5 a3 3 0 0 1-3 3 H8.5 L4.5 20 Z" />
    ),
    spark: [12, 10.8, 1.6],
  },

  // ── Utilitários (sem faísca — adaptam a cor do contexto) ────
  pin: {
    body: (
      <>
        <path d="M12 21c4.5-4.5 7-7.6 7-11a7 7 0 1 0-14 0c0 3.4 2.5 6.5 7 11z" />
        <circle cx="12" cy="10" r="2.6" />
      </>
    ),
  },
  check: { body: <path d="M4.5 12.5 L9.5 17.5 L19.5 6.5" /> },
  close: { body: <path d="M6 6 L18 18 M18 6 L6 18" /> },
  warning: {
    body: (
      <>
        <path d="M12 3.6 L21.4 19.8 a1 1 0 0 1-0.87 1.5 H3.47 a1 1 0 0 1-0.87-1.5 Z" />
        <line x1="12" y1="9.6" x2="12" y2="14" />
        <path d="M12 17.2 h0.012" />
      </>
    ),
  },
  hourglass: {
    body: (
      <>
        <path d="M6.5 3.5h11 M6.5 20.5h11" />
        <path d="M7 3.5c0 4 4 4.5 5 8.5 1-4 5-4.5 5-8.5" />
        <path d="M7 20.5c0-4 4-4.5 5-8.5 1 4 5 4.5 5 8.5" />
      </>
    ),
  },
  document: {
    body: (
      <>
        <path d="M13 3.5H7a1.5 1.5 0 0 0-1.5 1.5v14a1.5 1.5 0 0 0 1.5 1.5h10a1.5 1.5 0 0 0 1.5-1.5V9z" />
        <path d="M13 3.5V9h5.5" />
        <line x1="8.5" y1="13" x2="15.5" y2="13" />
        <line x1="8.5" y1="16" x2="13.5" y2="16" />
      </>
    ),
  },
  wave: {
    body: (
      <>
        <path d="M9 11.5V6.6a1.2 1.2 0 0 1 2.4 0V11 M11.4 11V5.8a1.2 1.2 0 0 1 2.4 0V11 M13.8 11V6.8a1.2 1.2 0 0 1 2.4 0v6.4a5.4 5.4 0 0 1-5.4 5.4 4.6 4.6 0 0 1-3.9-2.2l-2-3.2a1.25 1.25 0 0 1 2.05-1.4L9 13.2" />
        <path d="M16 4.6l1-1.1 M18.2 6.4l1.3-.6 M18.8 9.3l1.4.1" />
      </>
    ),
  },
  celebrate: {
    body: (
      <>
        <path d="M3.5 20.5 L9 8.5 L15.5 15 Z" />
        <path d="M14 6V4 M16.8 7.2l1.4-1.4 M17.8 11l2-.6" />
        <circle cx="16.4" cy="9.6" r="0.5" fill={fill} stroke="none" />
      </>
    ),
  },
  flame: {
    body: (
      <path d="M12 3c.6 3.5 4 4.6 4 8.5a4 4 0 0 1-8 0c0-1.7.8-2.9 1.6-3.9.3 1 .9 1.5 1.6 1.3C10.4 6.5 11 4.4 12 3z" />
    ),
  },
  lock: {
    body: (
      <>
        <rect x="5" y="10.5" width="14" height="9.5" rx="2" />
        <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" />
        <line x1="12" y1="14.5" x2="12" y2="16.5" />
      </>
    ),
  },
  camera: {
    body: (
      <>
        <path d="M3.5 8.5h3l1.5-2h6l1.5 2h3a1.5 1.5 0 0 1 1.5 1.5v8.5a1.5 1.5 0 0 1-1.5 1.5H3.5A1.5 1.5 0 0 1 2 18.5V10a1.5 1.5 0 0 1 1.5-1.5z" />
        <circle cx="12" cy="13.5" r="3.2" />
      </>
    ),
  },
  eye: {
    body: (
      <>
        <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
        <circle cx="12" cy="12" r="2.8" />
      </>
    ),
  },
  tent: {
    body: (
      <>
        <path d="M3 20 V11 a9 9 0 0 1 18 0 v9" />
        <line x1="2.5" y1="20.5" x2="21.5" y2="20.5" />
        <path d="M12 9 L8.5 20 M12 9 L15.5 20" />
      </>
    ),
  },
  external: {
    body: (
      <>
        <path d="M14 4h6v6" />
        <path d="M20 4 L11 13" />
        <path d="M18 13.5V19a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 19V8a1.5 1.5 0 0 1 1.5-1.5H11" />
      </>
    ),
  },
  sparkle: {
    body: (
      <>
        <path
          d="M12 3 L13.5 10.3 L21 12 L13.5 13.7 L12 21 L10.5 13.7 L3 12 L10.5 10.3 Z"
          fill={fill}
          stroke="none"
        />
        <path d="M18.5 4 v2.6 M17.2 5.3 h2.6" />
      </>
    ),
  },
  menu: {
    body: (
      <>
        <line x1="4" y1="7" x2="20" y2="7" />
        <line x1="4" y1="12" x2="20" y2="12" />
        <line x1="4" y1="17" x2="20" y2="17" />
      </>
    ),
  },
  power: {
    body: (
      <>
        <path d="M12 3.5V11" />
        <path d="M7.5 6.6a8 8 0 1 0 9 0" />
      </>
    ),
  },
  grid: {
    body: (
      <>
        <rect x="3.5" y="3.5" width="7" height="7" rx="1.4" />
        <rect x="13.5" y="3.5" width="7" height="7" rx="1.4" />
        <rect x="3.5" y="13.5" width="7" height="7" rx="1.4" />
        <rect x="13.5" y="13.5" width="7" height="7" rx="1.4" />
      </>
    ),
  },
  bolt: {
    body: (
      <path
        d="M13 2.5 L4.8 13.2 a0.6 0.6 0 0 0 0.48 0.96 H10 L9.2 21.2 a0.5 0.5 0 0 0 0.9 0.36 L19.2 10.8 a0.6 0.6 0 0 0-0.48-0.96 H13.5 L14.6 3 a0.5 0.5 0 0 0-0.9-0.36z"
        fill={fill}
        stroke="none"
      />
    ),
  },
};

type IconProps = {
  name: IconName;
  /** Adiciona a faísca dourada da marca (só ícones de feature têm posição). */
  spark?: boolean;
  /** Tamanho em px. Padrão: 1em (acompanha o texto). */
  size?: number;
  className?: string;
  style?: CSSProperties;
  /** Rótulo acessível; quando ausente, o ícone é `aria-hidden`. */
  title?: string;
};

export const Icon = ({ name, spark = false, size, className, style, title }: IconProps) => {
  const def = ICONS[name];
  const dim = size ?? "1em";
  return (
    <svg
      viewBox="0 0 24 24"
      width={dim}
      height={dim}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{ display: "inline-block", verticalAlign: "-0.125em", flexShrink: 0, ...style }}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      focusable="false"
    >
      {title ? <title>{title}</title> : null}
      {def.body}
      {spark && def.spark ? (
        <Spark x={def.spark[0]} y={def.spark[1]} s={def.spark[2]} />
      ) : null}
    </svg>
  );
};
