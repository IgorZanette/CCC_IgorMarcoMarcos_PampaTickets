import { useState } from "react";
import { AxiosError } from "axios";
import { Link, useNavigate } from "react-router-dom";

import { login, reenviarConfirmacao } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { toastInfo } from "../../lib/toast";
import { Icon } from "../../components/Icon";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

// O backend responde 403 com esta mensagem quando o e-mail ainda não foi
// confirmado — diferente de "Conta desativada." (também 403).
const ehEmailNaoConfirmado = (err: unknown): boolean =>
  err instanceof AxiosError &&
  err.response?.status === 403 &&
  /n[ãa]o confirmad/i.test(
    String((err.response.data as { detail?: string } | undefined)?.detail ?? ""),
  );

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
      if (ehEmailNaoConfirmado(err)) {
        // Leva ao fluxo de confirmação (campo de código + botão de reenviar) e
        // já dispara um novo código, caso o do cadastro tenha expirado.
        reenviarConfirmacao({ email }).catch(() => undefined);
        toastInfo("Confirme seu e-mail para entrar. Enviamos um novo código.");
        navigate("/confirmar-email", { state: { email, senha } });
        return;
      }
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
        {error && (
          <div className={forms.error}>
            <Icon name="warning" /> {error}
          </div>
        )}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Entrando…" : "Entrar →"}
        </button>
        <Link
          to="/esqueci-senha"
          style={{
            textAlign: "center",
            color: "var(--pt-accent)",
            fontWeight: 600,
            fontSize: 13,
            textDecoration: "none",
            marginTop: 4,
          }}
        >
          Esqueci minha senha
        </Link>
      </form>
    </AuthShell>
  );
};
