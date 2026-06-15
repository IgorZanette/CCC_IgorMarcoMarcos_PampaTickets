import styles from "./PampaBackdrop.module.css";

/**
 * Fundo translúcido e cultural da landing — posicionado SÓ nas bordas/cantos
 * vazios, deixando o centro livre para o conteúdo. Conta a história da marca:
 *
 *  • o globo dourado saindo do canto = o mundo que o PampaTickets quer alcançar;
 *  • a constelação de raios = eventos se acendendo e conectando pelo mundo;
 *  • as coxilhas e os relevos convergindo ao horizonte (a assinatura da logo)
 *    = "do nosso pampa pro mundo";
 *  • o chimarrão = a cultura gaúcha do RS.
 *
 * Verde-pampa via `currentColor`; dourado (mundo/energia) via `style`.
 */

const gold = { fill: "var(--pt-accent-hot)" } as const;
const goldStroke = { stroke: "var(--pt-accent-hot)" } as const;

const Bolt = ({ x, y, s, o }: { x: number; y: number; s: number; o: number }) => (
  <path
    transform={`translate(${x} ${y}) scale(${s})`}
    d="M0.18 -1L-0.62 0.16L-0.04 0.16L-0.18 1L0.62 -0.16L0.04 -0.16Z"
    style={gold}
    stroke="none"
    opacity={o}
  />
);

// Constelação (canto superior-direito, descendo para o vão lateral)
const NODES: [number, number, number][] = [
  [250, 300, 12],
  [140, 415, 8],
  [310, 430, 9],
  [80, 320, 7],
  [360, 330, 10],
];
const LINKS: [number, number][] = [
  [3, 0],
  [0, 4],
  [0, 2],
  [3, 1],
  [1, 2],
];

export const PampaBackdrop = () => (
  <>
    {/* ── O mundo + constelação de eventos — canto superior-direito ── */}
    <svg
      className={styles.world}
      viewBox="0 0 560 560"
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ color: "var(--pt-accent)" }}
    >
      <defs>
        <clipPath id="pt-world">
          <circle cx="400" cy="180" r="150" />
        </clipPath>
      </defs>
      <circle cx="400" cy="180" r="150" style={goldStroke} opacity={0.08} />
      <g clipPath="url(#pt-world)" style={goldStroke} opacity={0.06}>
        <ellipse cx="400" cy="180" rx="52" ry="150" />
        <ellipse cx="400" cy="180" rx="104" ry="150" />
        <line x1="262" y1="102" x2="538" y2="102" />
        <line x1="252" y1="180" x2="548" y2="180" />
        <line x1="262" y1="258" x2="538" y2="258" />
      </g>

      <g style={goldStroke} opacity={0.05}>
        {LINKS.map(([a, b], i) => (
          <line
            key={i}
            x1={NODES[a][0]}
            y1={NODES[a][1]}
            x2={NODES[b][0]}
            y2={NODES[b][1]}
          />
        ))}
      </g>
      {NODES.map(([x, y, s], i) => (
        <Bolt key={i} x={x} y={y} s={s} o={0.08} />
      ))}
    </svg>

    {/* ── Coxilhas + relevos do pampa convergindo ao mundo — faixa inferior ── */}
    <svg
      className={styles.pampa}
      viewBox="0 0 1440 440"
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ color: "var(--pt-accent)" }}
    >
      {/* relevos convergindo ao horizonte, apontando ao mundo (canto sup. dir.) */}
      <g opacity={0.07}>
        <path d="M-40 440 C 320 340 780 170 1150 46" />
        <path d="M260 440 C 540 350 880 178 1160 44" />
        <path d="M580 440 C 760 352 980 188 1168 42" />
        <path d="M900 440 C 1010 352 1092 196 1174 40" />
      </g>
      {/* fileiras do campo */}
      <g opacity={0.045}>
        <path d="M0 292 C 400 264 1040 264 1440 292" />
        <path d="M0 352 C 400 327 1040 327 1440 352" />
      </g>
      {/* coxilhas (três camadas) */}
      <path
        fill="currentColor"
        stroke="none"
        opacity={0.04}
        d="M0 296 C 300 268 560 292 820 278 S 1240 298 1440 272 L1440 440 L0 440 Z"
      />
      <path
        fill="currentColor"
        stroke="none"
        opacity={0.06}
        d="M0 348 C 360 320 640 344 900 328 S 1280 350 1440 320 L1440 440 L0 440 Z"
      />
      <path
        fill="currentColor"
        stroke="none"
        opacity={0.08}
        d="M0 402 C 400 376 680 400 940 386 S 1300 406 1440 382 L1440 440 L0 440 Z"
      />
    </svg>

    {/* ── Chimarrão — canto inferior-esquerdo (cultura gaúcha) ── */}
    <svg
      className={styles.chimarrao}
      viewBox="0 0 120 132"
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ color: "var(--pt-accent)" }}
      opacity={0.11}
    >
      <path d="M12 56 C12 100 38 122 60 122 C82 122 108 100 108 56 C108 50 104 46 98 46 L22 46 C16 46 12 50 12 56 Z" />
      <path d="M18 49 Q60 35 102 49" />
      <line x1="72" y1="54" x2="106" y2="14" />
      <circle cx="108" cy="11" r="4" />
    </svg>
  </>
);
