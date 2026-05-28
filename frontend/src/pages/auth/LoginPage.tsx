import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { login } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

export const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const usuario = await login({ email, senha });
      navigate(usuario.perfil === "ORGANIZADOR" ? "/organizador" : "/inicio");
    } catch (err: unknown) {
      setError(
        extractErrorMessage(
          err,
          "Não foi possível entrar. Verifique suas credenciais.",
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Entrar"
      subtitle="Acesse sua conta participante ou organizadora."
      footer={
        <>
          Ainda não tem conta?{" "}
          <Link to="/cadastro" style={{ color: "var(--pt-accent)", fontWeight: 600 }}>
            Cadastre-se
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className={forms.field} style={{ gap: 14 }}>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="email">
            E-mail
          </label>
          <input
            id="email"
            type="email"
            className={forms.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="voce@email.com"
            required
            autoFocus
          />
        </div>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="senha">
            Senha
          </label>
          <input
            id="senha"
            type="password"
            className={forms.input}
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        {error && <div className={forms.error}>⚠ {error}</div>}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Entrando…" : "Entrar →"}
        </button>
      </form>
      <div
        style={{
          fontSize: 12,
          color: "var(--pt-text-dim)",
          textAlign: "center",
          marginTop: 12,
        }}
      >
        Sem backend rodando? Use{" "}
        <Link to="/inicio" style={{ color: "var(--pt-accent)" }}>
          /inicio
        </Link>{" "}
        ou{" "}
        <Link to="/organizador" style={{ color: "var(--pt-accent)" }}>
          /organizador
        </Link>{" "}
        para ver o demo.
      </div>
    </AuthShell>
  );
};
