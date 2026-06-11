// Guard de rota: sem login → /login; perfil errado → /inicio; ok → renderiza.

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import type { Usuario } from "../api/auth";
import { setStoredUser } from "../lib/auth-store";
import { RequireAuth } from "./RequireAuth";

const usuario = (perfil: Usuario["perfil"]): Usuario => ({
  id: "u-1",
  nome: "Maria Silva",
  email: "maria@example.com",
  cpf_cnpj: "12345678901",
  celular: "54999998888",
  perfil,
  ativo: true,
  criado_em: "2026-01-01T00:00:00Z",
});

const App = ({ perfil }: { perfil?: Usuario["perfil"] }) => (
  <MemoryRouter initialEntries={["/protegida"]}>
    <Routes>
      <Route path="/login" element={<div>Tela de login</div>} />
      <Route path="/inicio" element={<div>Vitrine</div>} />
      <Route element={<RequireAuth perfil={perfil} />}>
        <Route path="/protegida" element={<div>Conteúdo protegido</div>} />
      </Route>
    </Routes>
  </MemoryRouter>
);

afterEach(() => {
  setStoredUser(null);
});

describe("RequireAuth", () => {
  it("redireciona visitante para /login", () => {
    render(<App />);
    expect(screen.getByText("Tela de login")).toBeInTheDocument();
  });

  it("renderiza o conteúdo para usuário logado", () => {
    setStoredUser(usuario("PARTICIPANTE"));
    render(<App />);
    expect(screen.getByText("Conteúdo protegido")).toBeInTheDocument();
  });

  it("redireciona para /inicio quando o perfil não bate", () => {
    setStoredUser(usuario("PARTICIPANTE"));
    render(<App perfil="ORGANIZADOR" />);
    expect(screen.getByText("Vitrine")).toBeInTheDocument();
  });

  it("permite acesso quando o perfil exigido bate", () => {
    setStoredUser(usuario("ORGANIZADOR"));
    render(<App perfil="ORGANIZADOR" />);
    expect(screen.getByText("Conteúdo protegido")).toBeInTheDocument();
  });
});
