// Cliente axios para o backend FastAPI.
// Token JWT é guardado em localStorage; injetado automaticamente em cada request.

import axios, { type AxiosInstance } from "axios";

import { setStoredUser } from "../lib/auth-store";

const baseURL =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  "http://localhost:8000/api";

export const TOKEN_KEY = "pt_token";

// Renova o token quando faltar menos que isso para expirar (token de 60min).
const REFRESH_BEFORE_MS = 20 * 60 * 1000;

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 8000,
});

// Instante de expiração do JWT em ms — null se o token for ilegível.
export const tokenExpMs = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as { exp?: number };
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

// Renovação deslizante (single-flight): perto de expirar, troca o token via
// POST /auth/refresh antes de seguir com a request. Usa axios cru para não
// passar pelos interceptors (evitaria recursão). Falha de renovação não
// bloqueia a request — o fluxo de 401 abaixo é o fallback.
let refreshing: Promise<void> | null = null;

const renovarSePreciso = (): Promise<void> => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return Promise.resolve();
  const exp = tokenExpMs(token);
  if (exp === null || exp <= Date.now() || exp - Date.now() > REFRESH_BEFORE_MS) {
    return Promise.resolve();
  }
  refreshing ??= axios
    .post<{ access_token: string }>(`${baseURL}/auth/refresh`, null, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 8000,
    })
    .then(({ data }) => setToken(data.access_token))
    .catch(() => undefined)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
};

api.interceptors.request.use(async (config) => {
  await renovarSePreciso();
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Sessão expirada/inválida (401): limpa token + usuário. Os guards de rota
// (RequireAuth) reagem à mudança e redirecionam para /login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      setToken(null);
      setStoredUser(null);
    }
    return Promise.reject(error);
  },
);

export const setToken = (token: string | null) => {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
};

export const getToken = () => localStorage.getItem(TOKEN_KEY);
