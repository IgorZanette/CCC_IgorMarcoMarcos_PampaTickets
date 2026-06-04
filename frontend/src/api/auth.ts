// Auth: login e cadastro contra o backend FastAPI.

import { setStoredUser } from "../lib/auth-store";
import { api, setToken } from "./client";

export type Perfil = "PARTICIPANTE" | "ORGANIZADOR";

export type Usuario = {
  id: string;
  nome: string;
  email: string;
  cpf_cnpj: string;
  celular: string;
  perfil: Perfil;
  ativo: boolean;
  criado_em: string;
};

export type LoginPayload = {
  email: string;
  senha: string;
};

export type CadastroPayload = {
  nome: string;
  email: string;
  cpf_cnpj: string;
  celular: string;
  senha: string;
  perfil: Perfil;
};

export const login = async (payload: LoginPayload): Promise<Usuario> => {
  const { data } = await api.post<{ access_token: string; usuario: Usuario }>(
    "/auth/login",
    payload,
  );
  setToken(data.access_token);
  setStoredUser(data.usuario);
  return data.usuario;
};

export const cadastro = async (payload: CadastroPayload): Promise<Usuario> => {
  const { data } = await api.post<Usuario>("/auth/cadastro", payload);
  return data;
};

export const me = async (): Promise<Usuario> => {
  const { data } = await api.get<Usuario>("/auth/me");
  setStoredUser(data);
  return data;
};

export const logout = () => {
  setToken(null);
  setStoredUser(null);
};
