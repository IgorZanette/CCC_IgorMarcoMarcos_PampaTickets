// Formatadores pt-BR — a convenção do app (#15) é exibir datas no fuso de
// São Paulo independente do fuso do navegador/CI, então os testes usam ISOs
// em UTC e esperam a conversão para UTC-3.

import { describe, expect, it } from "vitest";

import {
  dateFull,
  dateLong,
  formatCelular,
  formatCpfCnpj,
  localToUtcIso,
  money,
} from "./format";

describe("money", () => {
  it("formata valores em reais com duas casas", () => {
    // toLocaleString pt-BR usa NBSP em alguns ambientes — normalizamos espaços.
    expect(money(1234.5).replace(/\u00a0/g, " ")).toBe("R$ 1.234,50");
  });

  it("exibe Grátis para zero", () => {
    expect(money(0)).toBe("Grátis");
  });
});

describe("datas no fuso de São Paulo", () => {
  it("converte meia-noite UTC para a noite anterior em SP", () => {
    // 2026-07-01T00:30Z = 2026-06-30 21:30 em São Paulo (UTC-3).
    expect(dateLong("2026-07-01T00:30:00Z")).toContain("30");
    expect(dateLong("2026-07-01T00:30:00Z")).toContain("junho");
  });

  it("dateFull devolve as partes no fuso de SP", () => {
    const parts = dateFull("2026-07-01T00:30:00Z");
    expect(parts.dia).toBe("30");
    expect(parts.mes).toBe("JUN");
    expect(parts.hora).toBe("21:30");
    expect(parts.ano).toBe(2026);
  });
});

describe("localToUtcIso", () => {
  it("interpreta o datetime-local como horário de SP e devolve UTC", () => {
    expect(localToUtcIso("2026-12-31T20:00")).toBe("2026-12-31T23:00:00.000Z");
  });
});

describe("documentos e telefone", () => {
  it("formata CPF", () => {
    expect(formatCpfCnpj("12345678901")).toBe("123.456.789-01");
  });

  it("formata CNPJ", () => {
    expect(formatCpfCnpj("12345678000195")).toBe("12.345.678/0001-95");
  });

  it("devolve o valor original quando o tamanho não bate", () => {
    expect(formatCpfCnpj("123")).toBe("123");
  });

  it("formata celular com 11 dígitos", () => {
    expect(formatCelular("54999998888")).toBe("(54) 99999-8888");
  });

  it("formata fixo com 10 dígitos", () => {
    expect(formatCelular("5433334444")).toBe("(54) 3333-4444");
  });
});
