// Formatadores em pt-BR — moeda, datas, helpers para datas laterais.
// Convenção do app (#15): datas são exibidas e digitadas no fuso de São Paulo
// (UTC-3, sem horário de verão desde 2019), independentemente do fuso do navegador.

const TZ = "America/Sao_Paulo";

export const money = (v: number): string =>
  v === 0
    ? "Grátis"
    : "R$ " +
      Number(v).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });

export const moneyShort = (v: number): string =>
  v === 0
    ? "Grátis"
    : "R$ " + Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 0 });

export const dateShort = (iso: string): string => {
  const d = new Date(iso);
  return d
    .toLocaleDateString("pt-BR", { timeZone: TZ, day: "2-digit", month: "short" })
    .replace(".", "");
};

export const dateLong = (iso: string): string => {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", {
    timeZone: TZ,
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
};

export const formatCpfCnpj = (raw: string): string => {
  const d = (raw || "").replace(/\D/g, "");
  if (d.length === 11) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  if (d.length === 14)
    return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
  return raw;
};

export const formatCelular = (raw: string): string => {
  const d = (raw || "").replace(/\D/g, "");
  if (d.length === 11) return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
  if (d.length === 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return raw;
};

export type DateParts = {
  dia: string;
  mes: string;
  semana: string;
  ano: number;
  hora: string;
};

export const dateFull = (iso: string): DateParts => {
  const d = new Date(iso);
  return {
    dia: d.toLocaleDateString("pt-BR", { timeZone: TZ, day: "2-digit" }),
    mes: d
      .toLocaleDateString("pt-BR", { timeZone: TZ, month: "short" })
      .replace(".", "")
      .toUpperCase(),
    semana: d
      .toLocaleDateString("pt-BR", { timeZone: TZ, weekday: "short" })
      .replace(".", "")
      .toUpperCase(),
    ano: Number(d.toLocaleDateString("pt-BR", { timeZone: TZ, year: "numeric" })),
    hora: d.toLocaleTimeString("pt-BR", {
      timeZone: TZ,
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
};

// Interpreta um valor de <input type="datetime-local"> (ex.: "2026-12-31T20:00")
// como horário de São Paulo (UTC-3) e devolve o ISO em UTC para enviar ao backend.
// Garante a mesma convenção em todos os formulários, independente do fuso do navegador.
export const localToUtcIso = (value: string): string => {
  const comSegundos = value.length === 16 ? `${value}:00` : value;
  return new Date(`${comSegundos}-03:00`).toISOString();
};

// Inverso de `localToUtcIso`: recebe um ISO em UTC (vindo do backend) e devolve
// o valor "YYYY-MM-DDTHH:mm" para pré-preencher um <input type="datetime-local">
// no fuso de São Paulo. Usado ao editar entidades que já têm datas salvas.
export const utcIsoToLocalInput = (iso: string): string => {
  const d = new Date(iso);
  const data = d.toLocaleDateString("en-CA", { timeZone: TZ }); // YYYY-MM-DD
  const hora = d.toLocaleTimeString("en-GB", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
  }); // HH:mm
  return `${data}T${hora}`;
};
