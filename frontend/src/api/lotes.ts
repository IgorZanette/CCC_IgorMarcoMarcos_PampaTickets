// Lotes — UC03. Listagem pública por evento e contexto do organizador.

import { api } from "./client";

export type TipoLote = "INTEIRA" | "MEIA" | "PROMOCIONAL";

export type Lote = {
  id: string;
  evento_id: string;
  nome: string;
  tipo: TipoLote;
  preco: number;
  quantidade_total: number;
  quantidade_vendida: number;
  quantidade_disponivel: number;
  data_inicio_venda: string;
  data_fim_venda: string;
  ativo: boolean;
  criado_em: string;
};

export type LoteCreate = {
  nome: string;
  tipo: TipoLote;
  preco: number;
  quantidade_total: number;
  data_inicio_venda: string;
  data_fim_venda: string;
  ativo?: boolean;
};

export type LoteUpdate = Partial<Omit<LoteCreate, "ativo">>;

export const listarLotes = async (eventoId: string): Promise<Lote[]> => {
  const { data } = await api.get<Lote[]>(`/eventos/${eventoId}/lotes`);
  return data;
};

export const listarLotesOrganizador = async (eventoId: string): Promise<Lote[]> => {
  const { data } = await api.get<Lote[]>(
    `/organizador/eventos/${eventoId}/lotes`,
  );
  return data;
};

export const criarLote = async (
  eventoId: string,
  payload: LoteCreate,
): Promise<Lote> => {
  const { data } = await api.post<Lote>(`/eventos/${eventoId}/lotes`, payload);
  return data;
};

export const editarLote = async (
  loteId: string,
  payload: LoteUpdate,
): Promise<Lote> => {
  const { data } = await api.put<Lote>(`/lotes/${loteId}`, payload);
  return data;
};

export const ativarLote = async (loteId: string): Promise<Lote> => {
  const { data } = await api.patch<Lote>(`/lotes/${loteId}/ativar`);
  return data;
};

export const desativarLote = async (loteId: string): Promise<Lote> => {
  const { data } = await api.patch<Lote>(`/lotes/${loteId}/desativar`);
  return data;
};

export const deletarLote = async (loteId: string): Promise<void> => {
  await api.delete(`/lotes/${loteId}`);
};
