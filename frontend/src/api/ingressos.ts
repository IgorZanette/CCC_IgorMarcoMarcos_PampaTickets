// Ingressos — UC07/UC12. Cada ingresso traz dados desnormalizados de evento/lote
// pra montar a tela "Meus ingressos" sem joins extras.

import { api } from "./client";

export type StatusIngresso = "ATIVO" | "UTILIZADO" | "CANCELADO";

export type Ingresso = {
  id: string;
  qr_code_hash: string;
  status: StatusIngresso;
  pdf_url: string | null;
  emitido_em: string;
  evento_nome: string;
  evento_data_inicio: string;
  evento_local: string;
  lote_nome: string;
};

export const listarMeusIngressos = async (): Promise<Ingresso[]> => {
  const { data } = await api.get<Ingresso[]>("/ingressos/meus");
  return data;
};

export const obterIngresso = async (ingressoId: string): Promise<Ingresso> => {
  const { data } = await api.get<Ingresso>(`/ingressos/${ingressoId}`);
  return data;
};
