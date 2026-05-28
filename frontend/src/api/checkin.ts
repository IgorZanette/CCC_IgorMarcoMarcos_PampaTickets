// Check-in via QR Code — UC04. Apenas organizador autenticado.

import { api } from "./client";

export type CheckinRequest = {
  qr_code_hash: string;
};

export type CheckinResponse = {
  checkin_id: string;
  ingresso_id: string;
  realizado_em: string;
};

export const realizarCheckin = async (
  payload: CheckinRequest,
): Promise<CheckinResponse> => {
  const { data } = await api.post<CheckinResponse>("/checkin", payload);
  return data;
};
