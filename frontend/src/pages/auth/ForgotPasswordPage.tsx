import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { solicitarRecuperacaoSenha } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

export const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await solicitarRecuperacaoSenha({ email });
      setSuccess(true);
      // Redirecionar após 2 segundos
      setTimeout(() => {
        navigate("/validar-codigo", { state: { email } });
      }, 2000);
    } catch (err: unknown) {
      setError(
        extractErrorMessage(
          err,
          "Não foi possível enviar o código. Tente novamente.",
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <AuthShell
        title="Código Enviado"
        subtitle="Verifique seu email para o código de 6 dígitos."
        footer={
          <>
            <p style={{ textAlign: "center", color: "var(--pt-text-dim)", fontSize: 14 }}>
              Redirecionando para validação...
            </p>
          </>
        }
      >
        <div style={{ textAlign: "center", padding: "20px 0" }}>
          <p style={{ color: "var(--pt-success)", fontSize: 14, fontWeight: 600 }}>
            ✓ Email enviado com sucesso para {email}
          </p>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Esqueci Minha Senha"
      subtitle="Informe seu email para receber um código de recuperação."
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
        {error && <div className={forms.error}>⚠ {error}</div>}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Enviando…" : "Enviar Código →"}
        </button>
      </form>
    </AuthShell>
  );
};
