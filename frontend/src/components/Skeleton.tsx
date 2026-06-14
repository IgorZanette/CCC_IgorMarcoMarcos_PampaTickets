import styles from "./Skeleton.module.css";

type SkeletonProps = {
  width?: number | string;
  height?: number | string;
  radius?: number | string;
  className?: string;
};

// Bloco "fantasma" pulsante — placeholder de conteúdo durante o carregamento.
export const Skeleton = ({ width, height, radius, className }: SkeletonProps) => (
  <div
    className={`${styles.skeleton} ${className ?? ""}`}
    style={{ width, height, borderRadius: radius }}
  />
);

// Card-esqueleto pronto (capa + linhas) para grades de eventos/ingressos.
export const SkeletonCard = () => (
  <div className={styles.card}>
    <Skeleton className={styles.cover} />
    <Skeleton className={styles.line} width="70%" />
    <Skeleton className={styles.line} width="45%" />
  </div>
);

// Repete N SkeletonCards — atalho para preencher uma grade enquanto carrega.
export const SkeletonGrid = ({ count = 6 }: { count?: number }) => (
  <>
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </>
);
