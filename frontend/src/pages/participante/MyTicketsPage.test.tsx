// Fluxo de reembolso (UC10) na tela "Meus ingressos": botão → modal → envio,
// estados vindos do backend (reembolso_solicitado), cortesias e erro 409.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, type AxiosResponse } from "axios";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Usuario } from "../../api/auth";
import { listarMeusIngressos, type Ingresso } from "../../api/ingressos";
import { reembolsarPedido, type Reembolso } from "../../api/pedidos";
import { setStoredUser } from "../../lib/auth-store";
import { MyTicketsPage } from "./MyTicketsPage";

vi.mock("../../api/ingressos", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/ingressos")>();
  return { ...mod, listarMeusIngressos: vi.fn() };
});

vi.mock("../../api/pedidos", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/pedidos")>();
  return { ...mod, reembolsarPedido: vi.fn() };
});

const participante: Usuario = {
  id: "u-1",
  nome: "Maria Silva",
  email: "maria@example.com",
  cpf_cnpj: "12345678901",
  celular: "54999998888",
  perfil: "PARTICIPANTE",
  ativo: true,
  criado_em: "2026-01-01T00:00:00Z",
};

const ingresso = (overrides: Partial<Ingresso> = {}): Ingresso => ({
  id: "ing-1",
  qr_code_hash: "hash-1",
  status: "ATIVO",
  pdf_url: null,
  emitido_em: "2026-06-01T00:00:00Z",
  evento_nome: "Festival do Pampa",
  // Evento futuro para cair na aba "Próximos eventos".
  evento_data_inicio: "2030-01-01T20:00:00Z",
  evento_local: "Passo Fundo",
  lote_nome: "Pista",
  pedido_id: "ped-1",
  reembolso_solicitado: false,
  ...overrides,
});

const reembolso: Reembolso = {
  id: "ree-1",
  pagamento_id: "pag-1",
  motivo: "Imprevisto",
  valor_reembolsado: 100,
  processado_em: null,
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <MyTicketsPage />
    </MemoryRouter>,
  );

beforeEach(() => {
  setStoredUser(participante);
});

afterEach(() => {
  setStoredUser(null);
  vi.clearAllMocks();
});

describe("MyTicketsPage — reembolso", () => {
  it("solicita o reembolso pelo modal e marca todos os ingressos do pedido", async () => {
    // Dois ingressos do mesmo pedido: a solicitação deve refletir em ambos.
    vi.mocked(listarMeusIngressos).mockResolvedValue([
      ingresso({ id: "ing-1" }),
      ingresso({ id: "ing-2", lote_nome: "Pista 2" }),
    ]);
    vi.mocked(reembolsarPedido).mockResolvedValue(reembolso);
    const user = userEvent.setup();

    renderPage();
    const botoes = await screen.findAllByRole("button", {
      name: "Solicitar reembolso",
    });
    expect(botoes).toHaveLength(2);
    await user.click(botoes[0]);

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/pedido inteiro/)).toBeInTheDocument();
    await user.type(
      within(dialog).getByLabelText("Motivo (opcional)"),
      "Imprevisto",
    );
    await user.click(
      within(dialog).getByRole("button", { name: "Confirmar reembolso" }),
    );

    expect(reembolsarPedido).toHaveBeenCalledWith("ped-1", {
      motivo: "Imprevisto",
    });
    const marcados = await screen.findAllByText(/Reembolso solicitado/);
    expect(marcados).toHaveLength(2);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Solicitar reembolso" }),
    ).not.toBeInTheDocument();
  });

  it("envia motivo null quando o campo fica vazio", async () => {
    vi.mocked(listarMeusIngressos).mockResolvedValue([ingresso()]);
    vi.mocked(reembolsarPedido).mockResolvedValue(reembolso);
    const user = userEvent.setup();

    renderPage();
    await user.click(
      await screen.findByRole("button", { name: "Solicitar reembolso" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Confirmar reembolso" }),
    );

    expect(reembolsarPedido).toHaveBeenCalledWith("ped-1", { motivo: null });
  });

  it("mostra o estado vindo do backend e esconde o botão (sobrevive a reload)", async () => {
    vi.mocked(listarMeusIngressos).mockResolvedValue([
      ingresso({ reembolso_solicitado: true }),
    ]);

    renderPage();
    expect(
      await screen.findByText(/Reembolso solicitado/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Solicitar reembolso" }),
    ).not.toBeInTheDocument();
  });

  it("não oferece reembolso para cortesia (ingresso sem pedido)", async () => {
    vi.mocked(listarMeusIngressos).mockResolvedValue([
      ingresso({ pedido_id: null }),
    ]);

    renderPage();
    expect(await screen.findByText("Festival do Pampa")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Solicitar reembolso" }),
    ).not.toBeInTheDocument();
  });

  it("exibe o erro do backend no modal sem fechá-lo", async () => {
    vi.mocked(listarMeusIngressos).mockResolvedValue([ingresso()]);
    const conflito = new AxiosError("Conflict");
    conflito.response = {
      data: { detail: "Reembolso já solicitado para este pedido." },
    } as AxiosResponse;
    vi.mocked(reembolsarPedido).mockRejectedValue(conflito);
    const user = userEvent.setup();

    renderPage();
    await user.click(
      await screen.findByRole("button", { name: "Solicitar reembolso" }),
    );
    await user.click(
      screen.getByRole("button", { name: "Confirmar reembolso" }),
    );

    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText(/Reembolso já solicitado/),
    ).toBeInTheDocument();
  });
});
