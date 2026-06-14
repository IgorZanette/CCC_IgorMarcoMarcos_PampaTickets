import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { confirmarEmail, login, reenviarConfirmacao } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

type LocationState = { email: string; senha: string } | null;

export const ConfirmarEmailPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  const email = state?.email ?? "";
  const senha = state?.senha ?? "";

  const [codigo, setCodigo] = useState("");
  const [loading, setLoading] = useState(false);
  const [reenvioLoading, setReenvioLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reenvioMsg, setReenvioMsg] = useState<string | null>(null);

  if (!email) {
    navigate("/cadastro");
    return null;
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await confirmarEmail({ email, codigo });
      const usuario = await login({ email, senha });
      navigate(usuario.perfil === "ORGANIZADOR" ? "/organizador" : "/inicio");
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Código inválido ou expirado."));
    } finally {
      setLoading(false);
    }
  };

  const reenviar = async () => {
    setReenvioMsg(null);
    setError(null);
    setReenvioLoading(true);
    try {
      await reenviarConfirmacao({ email });
      setReenvioMsg("Novo código enviado! Verifique sua caixa de entrada.");
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Não foi possível reenviar o código."));
    } finally {
      setReenvioLoading(false);
    }
  };

  return (
    <AuthShell
      title="Confirme seu e-mail"
      subtitle={`Enviamos um código de 6 dígitos para ${email}. Insira abaixo para ativar sua conta.`}
      footer={
        <p style={{ textAlign: "center", fontSize: 13, color: "var(--pt-text-dim)" }}>
          Não recebeu?{" "}
          <button
            type="button"
            onClick={reenviar}
            disabled={reenvioLoading}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              color: "var(--pt-accent)",
              fontWeight: 600,
              fontSize: 13,
              cursor: reenvioLoading ? "not-allowed" : "pointer",
            }}
          >
            {reenvioLoading ? "Enviando…" : "Reenviar código"}
          </button>
        </p>
      }
    >
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="codigo">
            Código de 6 dígitos
          </label>
          <input
            id="codigo"
            type="text"
            className={forms.input}
            value={codigo}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, "").slice(0, 6);
              setCodigo(val);
            }}
            placeholder="000000"
            required
            autoFocus
            maxLength={6}
            inputMode="numeric"
            style={{ textAlign: "center", fontSize: 24, letterSpacing: 8, fontWeight: 600 }}
          />
        </div>

        {reenvioMsg && (
          <div style={{ color: "var(--pt-accent)", fontSize: 13, textAlign: "center" }}>
            {reenvioMsg}
          </div>
        )}
        {error && <div className={forms.error}>⚠ {error}</div>}

        <button type="submit" className={forms.primary} disabled={loading || codigo.length < 6}>
          {loading ? "Confirmando…" : "Confirmar e entrar →"}
        </button>
      </form>
    </AuthShell>
  );
};
