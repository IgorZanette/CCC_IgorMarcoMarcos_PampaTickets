// extractErrorMessage traduz os formatos de erro do FastAPI (detail string,
// array de violações Pydantic) e falhas de rede em mensagens amigáveis.

import { AxiosError, type AxiosResponse } from "axios";
import { describe, expect, it } from "vitest";

import { extractErrorMessage } from "./errors";

const FALLBACK = "Algo deu errado.";

const axiosErrorCom = (data: unknown): AxiosError => {
  const err = new AxiosError("Request failed");
  err.response = { data } as AxiosResponse;
  return err;
};

describe("extractErrorMessage", () => {
  it("usa o detail string do FastAPI (HTTPException)", () => {
    const err = axiosErrorCom({ detail: "Reembolso já solicitado para este pedido." });
    expect(extractErrorMessage(err, FALLBACK)).toBe(
      "Reembolso já solicitado para este pedido.",
    );
  });

  it("usa a primeira violação de um erro de validação Pydantic", () => {
    const err = axiosErrorCom({
      detail: [{ loc: ["body", "email"], msg: "E-mail inválido" }],
    });
    expect(extractErrorMessage(err, FALLBACK)).toBe("E-mail inválido");
  });

  it("remove o prefixo 'Value error, ' dos field_validators", () => {
    const err = axiosErrorCom({
      detail: [{ loc: ["body", "cpf_cnpj"], msg: "Value error, CPF inválido" }],
    });
    expect(extractErrorMessage(err, FALLBACK)).toBe("CPF inválido");
  });

  it("explica falha de conexão quando não há resposta", () => {
    const err = new AxiosError("Network Error");
    expect(extractErrorMessage(err, FALLBACK)).toContain(
      "Não foi possível conectar ao servidor",
    );
  });

  it("cai no fallback para erros que não são do axios", () => {
    expect(extractErrorMessage(new Error("boom"), FALLBACK)).toBe(FALLBACK);
  });

  it("cai no fallback quando o detail tem formato inesperado", () => {
    const err = axiosErrorCom({ detail: { estranho: true } });
    expect(extractErrorMessage(err, FALLBACK)).toBe(FALLBACK);
  });
});
