// avaliarLote espelha as regras de compra do backend (pedido_service.criar) —
// estes testes fixam o contrato para detectar divergência se um lado mudar.

import { describe, expect, it } from "vitest";

import type { Lote } from "../api/lotes";
import { avaliarLote } from "./lote";

const AGORA = new Date("2026-06-15T12:00:00Z");

const lote = (overrides: Partial<Lote> = {}): Lote => ({
  id: "lote-1",
  evento_id: "ev-1",
  nome: "Pista",
  tipo: "INTEIRA",
  preco: 100,
  quantidade_total: 50,
  quantidade_vendida: 10,
  quantidade_disponivel: 40,
  data_inicio_venda: "2026-06-01T00:00:00Z",
  data_fim_venda: "2026-06-30T23:59:59Z",
  ativo: true,
  criado_em: "2026-05-01T00:00:00Z",
  ...overrides,
});

describe("avaliarLote", () => {
  it("considera disponível um lote ativo, na janela e com estoque", () => {
    const r = avaliarLote(lote(), AGORA);
    expect(r).toEqual({
      disponivel: true,
      motivo: null,
      rotulo: null,
      restantes: 40,
    });
  });

  it("marca esgotado quando não há estoque", () => {
    const r = avaliarLote(lote({ quantidade_disponivel: 0 }), AGORA);
    expect(r.disponivel).toBe(false);
    expect(r.motivo).toBe("esgotado");
    expect(r.rotulo).toBe("Esgotado");
  });

  it("marca encerrado após o fim da janela de venda", () => {
    const r = avaliarLote(
      lote({ data_fim_venda: "2026-06-10T00:00:00Z" }),
      AGORA,
    );
    expect(r.motivo).toBe("encerrado");
    expect(r.rotulo).toBe("Vendas encerradas");
  });

  it("marca em breve antes do início da janela de venda", () => {
    const r = avaliarLote(
      lote({ data_inicio_venda: "2026-06-20T00:00:00Z" }),
      AGORA,
    );
    expect(r.motivo).toBe("nao_iniciado");
    expect(r.rotulo).toBe("Em breve");
  });

  it("marca indisponível quando o lote está inativo", () => {
    const r = avaliarLote(lote({ ativo: false }), AGORA);
    expect(r.motivo).toBe("inativo");
    expect(r.rotulo).toBe("Indisponível");
  });

  it("prioriza esgotado sobre encerrado no rótulo", () => {
    const r = avaliarLote(
      lote({ quantidade_disponivel: 0, data_fim_venda: "2026-06-10T00:00:00Z" }),
      AGORA,
    );
    expect(r.motivo).toBe("esgotado");
  });

  it("compara instantes em UTC independentemente do fuso", () => {
    // 11:59 UTC ainda está dentro da janela que abre 12:00 UTC.
    const r = avaliarLote(
      lote({ data_inicio_venda: "2026-06-15T12:00:01Z" }),
      AGORA,
    );
    expect(r.motivo).toBe("nao_iniciado");
  });
});
