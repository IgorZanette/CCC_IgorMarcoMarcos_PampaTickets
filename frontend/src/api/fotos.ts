// Galeria de Fotos — UC08 (v1 grátis). Organizador publica; usuários autenticados
// veem/baixam. As URLs vêm assinadas pelo backend (bucket privado).

import { api } from "./client";

export type Foto = {
  id: string;
  evento_id: string;
  url_thumbnail: string;
  url_original: string;
  publicado_em: string;
};

export const listarFotos = async (eventoId: string): Promise<Foto[]> => {
  const { data } = await api.get<Foto[]>(`/eventos/${eventoId}/fotos`);
  return data;
};

export const enviarFotos = async (
  eventoId: string,
  files: File[],
): Promise<Foto[]> => {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  // O axios detecta FormData e define o Content-Type multipart automaticamente.
  const { data } = await api.post<Foto[]>(`/eventos/${eventoId}/fotos`, form);
  return data;
};

export const excluirFoto = async (fotoId: string): Promise<void> => {
  await api.delete(`/fotos/${fotoId}`);
};
