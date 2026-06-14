// Wrapper sobre o Sonner — centraliza estilo e ícones consistentes com a marca.
// As páginas importam daqui (nunca direto do sonner) para manter o feedback uniforme.

import { toast } from "sonner";

import { extractErrorMessage } from "./errors";

export const toastSuccess = (mensagem: string) => toast.success(mensagem);

export const toastInfo = (mensagem: string) => toast(mensagem);

// Aceita tanto uma string pronta quanto um erro do axios (extrai a mensagem).
export const toastError = (erro: unknown, fallback = "Algo deu errado. Tente novamente.") => {
  const mensagem = typeof erro === "string" ? erro : extractErrorMessage(erro, fallback);
  return toast.error(mensagem);
};
