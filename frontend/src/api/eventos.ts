// Eventos — UC02. Públicos (PUBLICADO/ENCERRADO) e área do organizador.
//
// O backend não armazena imagem do evento — usamos um gradient determinístico
// por id pra manter os cards visualmente distintos sem dado real.

import { api } from "./client";

export type StatusEvento = "RASCUNHO" | "PUBLICADO" | "ENCERRADO" | "CANCELADO";

export type Evento = {
  id: string;
  organizador_id: string;
  nome: string;
  descricao: string | null;
  data_inicio: string;
  data_fim: string;
  local: string;
  status: StatusEvento;
  criado_em: string;
};

export type EventoCreate = {
  nome: string;
  descricao?: string | null;
  data_inicio: string;
  data_fim: string;
  local: string;
};

export type EventoUpdate = Partial<EventoCreate>;

const GRADIENT_PALETTE = [
  "linear-gradient(135deg, #0d2b30 0%, #1f5a4a 60%, #c9a13b 100%)",
  "linear-gradient(135deg, #2a0a0a 0%, #7a1f1f 50%, #d4a437 100%)",
  "linear-gradient(135deg, #1a0a0a 0%, #c8102e 70%, #ffd700 100%)",
  "linear-gradient(135deg, #2a0a3e 0%, #ff5e3a 60%, #ffd700 100%)",
  "linear-gradient(135deg, #0a3d2e 0%, #1a8060 100%)",
  "linear-gradient(135deg, #1a0a2e 0%, #7c3aed 60%, #ec4899 100%)",
  "linear-gradient(135deg, #0a1929 0%, #1565c0 60%, #00bcd4 100%)",
  "linear-gradient(135deg, #3e1a0a 0%, #ff7043 60%, #ffeb3b 100%)",
];

// Hash determinístico simples — mesmo id sempre gera o mesmo gradient.
export const gradientFor = (id: string): string => {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  }
  return GRADIENT_PALETTE[hash % GRADIENT_PALETTE.length];
};

export const cidadeFromLocal = (local: string): string =>
  local.split(",").slice(-1)[0]?.trim() ?? "—";

export const listarEventos = async (): Promise<Evento[]> => {
  const { data } = await api.get<Evento[]>("/eventos", { params: { limit: 50 } });
  return data;
};

export const obterEvento = async (id: string): Promise<Evento> => {
  const { data } = await api.get<Evento>(`/eventos/${id}`);
  return data;
};

export const listarEventosOrganizador = async (): Promise<Evento[]> => {
  const { data } = await api.get<Evento[]>("/organizador/eventos");
  return data;
};

// Contraparte privada de `obterEvento`: o organizador enxerga o próprio
// evento em qualquer status (incluindo RASCUNHO e CANCELADO).
export const obterEventoOrganizador = async (id: string): Promise<Evento> => {
  const { data } = await api.get<Evento>(`/organizador/eventos/${id}`);
  return data;
};

export const criarEvento = async (payload: EventoCreate): Promise<Evento> => {
  const { data } = await api.post<Evento>("/eventos", payload);
  return data;
};

export const editarEvento = async (
  id: string,
  payload: EventoUpdate,
): Promise<Evento> => {
  const { data } = await api.put<Evento>(`/eventos/${id}`, payload);
  return data;
};

export const publicarEvento = async (id: string): Promise<Evento> => {
  const { data } = await api.patch<Evento>(`/eventos/${id}/publicar`);
  return data;
};

export const encerrarEvento = async (id: string): Promise<Evento> => {
  const { data } = await api.patch<Evento>(`/eventos/${id}/encerrar`);
  return data;
};

export const cancelarEvento = async (id: string): Promise<Evento> => {
  const { data } = await api.patch<Evento>(`/eventos/${id}/cancelar`);
  return data;
};
