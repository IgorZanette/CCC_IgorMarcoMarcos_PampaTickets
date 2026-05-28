// Pedidos — UC07/UC09/UC10. Criação dispara cobrança no Asaas e devolve pix_qrcode.

import { api } from "./client";

export type MetodoPagamento = "PIX" | "CREDIT_CARD" | "BOLETO";

export type StatusPedido = "PENDENTE" | "PAGO" | "CANCELADO" | "REEMBOLSADO";

export type PedidoItemCreate = {
  lote_id: string;
  quantidade: number;
};

export type PedidoCreate = {
  evento_id: string;
  itens: PedidoItemCreate[];
  metodo: MetodoPagamento;
  cupom_codigo?: string | null;
};

export type PedidoItem = {
  id: string;
  pedido_id: string;
  lote_id: string;
  quantidade: number;
  preco_unitario: number;
};

export type Pedido = {
  id: string;
  participante_id: string;
  evento_id: string;
  valor_total: number;
  valor_desconto: number;
  status: StatusPedido;
  criado_em: string;
  itens: PedidoItem[];
};

export type PixQrCode = {
  encodedImage: string;
  payload: string;
  expirationDate?: string;
};

export type PedidoCriado = {
  pedido: Pedido;
  invoice_url: string;
  charge_id: string;
  pix_qrcode: PixQrCode | null;
};

export type ReembolsoCreate = {
  motivo: string;
};

export const criarPedido = async (payload: PedidoCreate): Promise<PedidoCriado> => {
  const { data } = await api.post<PedidoCriado>("/pedidos", payload);
  return data;
};

export const listarMeusPedidos = async (): Promise<Pedido[]> => {
  const { data } = await api.get<Pedido[]>("/pedidos/meus");
  return data;
};

export const obterPedido = async (pedidoId: string): Promise<Pedido> => {
  const { data } = await api.get<Pedido>(`/pedidos/${pedidoId}`);
  return data;
};

export const cancelarPedido = async (pedidoId: string): Promise<Pedido> => {
  const { data } = await api.post<Pedido>(`/pedidos/${pedidoId}/cancelar`);
  return data;
};

export const reembolsarPedido = async (
  pedidoId: string,
  payload: ReembolsoCreate,
): Promise<Pedido> => {
  const { data } = await api.post<Pedido>(
    `/pedidos/${pedidoId}/reembolso`,
    payload,
  );
  return data;
};
