import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { redefinirSenha } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

export const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "";
  const codigo = location.state?.codigo || "";

  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!email || !codigo) {
    navigate("/esqueci-senha");
    return null;
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (novaSenha !== confirmarSenha) {
      setError("As senhas não conferem.");
      return;
    }

    if (novaSenha.length < 8) {
      setError("A senha deve ter no mínimo 8 caracteres.");
      return;
    }

    if (!/[A-Za-z]/.test(novaSenha) || !/\d/.test(novaSenha)) {
      setError("A senha deve conter letras e números.");
      return;
    }

    setLoading(true);
    try {
      await redefinirSenha({ email, codigo, nova_senha: novaSenha });
      setSuccess(true);
      // Redirecionar após 3 segundos
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err: unknown) {
      setError(
        extractErrorMessage(err, "Não foi possível redefinir a senha. Tente novamente."),
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <AuthShell
        title="Senha Redefinida"
        subtitle="Sua senha foi alterada com sucesso."
        footer={
          <>
            <p style={{ textAlign: "center", color: "var(--pt-text-dim)", fontSize: 14 }}>
              Redirecionando para login...
            </p>
          </>
        }
      >
        <div style={{ textAlign: "center", padding: "20px 0" }}>
          <p style={{ color: "var(--pt-success)", fontSize: 14, fontWeight: 600 }}>
            ✓ Senha redefinida com sucesso
          </p>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Redefinir Senha"
      subtitle="Crie uma nova senha para sua conta."
      footer={
        <>
          Voltou para a memória?{" "}
          <Link to="/login" style={{ color: "var(--pt-accent)", fontWeight: 600 }}>
            Entrar
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className={forms.field} style={{ gap: 14 }}>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="nova-senha">
            Nova Senha
          </label>
          <input
            id="nova-senha"
            type="password"
            className={forms.input}
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            placeholder="••••••••"
            required
            autoFocus
          />
          <p style={{ fontSize: 12, color: "var(--pt-text-dim)", marginTop: 4 }}>
            Mínimo 8 caracteres, letras e números
          </p>
        </div>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="confirmar-senha">
            Confirmar Senha
          </label>
          <input
            id="confirmar-senha"
            type="password"
            className={forms.input}
            value={confirmarSenha}
            onChange={(e) => setConfirmarSenha(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        {error && <div className={forms.error}>⚠ {error}</div>}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Redefinindo…" : "Redefinir Senha →"}
        </button>
      </form>
    </AuthShell>
  );
};
