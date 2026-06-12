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

export type RecuperacaoSenhaPayload = {
  email: string;
};

export type ValidarCodigoPayload = {
  email: string;
  codigo: string;
};

export type RedefinirSenhaPayload = {
  email: string;
  // Token devolvido por /validate-reset-code — o código de 6 dígitos não
  // transita mais após a validação.
  token: string;
  nova_senha: string;
};

export const solicitarRecuperacaoSenha = async (
  payload: RecuperacaoSenhaPayload,
): Promise<{ mensagem: string }> => {
  const { data } = await api.post<{ mensagem: string }>(
    "/auth/forgot-password",
    payload,
  );
  return data;
};

export const validarCodigoRecuperacao = async (
  payload: ValidarCodigoPayload,
): Promise<{ token: string; mensagem: string }> => {
  const { data } = await api.post<{ token: string; mensagem: string }>(
    "/auth/validate-reset-code",
    payload,
  );
  return data;
};

export const redefinirSenha = async (
  payload: RedefinirSenhaPayload,
): Promise<{ mensagem: string }> => {
  const { data } = await api.post<{ mensagem: string }>(
    "/auth/reset-password",
    payload,
  );
  return data;
};
