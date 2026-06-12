import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { validarCodigoRecuperacao } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

export const ValidateCodePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "";

  const [codigo, setCodigo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!email) {
    navigate("/esqueci-senha");
    return null;
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { token } = await validarCodigoRecuperacao({ email, codigo });
      // Daqui em diante quem autoriza o reset é o token — o código de 6
      // dígitos não transita mais (nem fica no history state do navegador).
      navigate("/redefinir-senha", { state: { email, token } });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Código inválido ou expirado."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Validar Código"
      subtitle="Digite o código de 6 dígitos enviado para seu email."
      footer={
        <>
          <p style={{ textAlign: "center", color: "var(--pt-text-dim)", fontSize: 13 }}>
            Email: <strong>{email}</strong>
          </p>
          <p style={{ textAlign: "center", fontSize: 13 }}>
            Não recebeu ou o código foi bloqueado?{" "}
            <Link
              to="/esqueci-senha"
              style={{ color: "var(--pt-accent)", fontWeight: 600 }}
            >
              Solicitar novo código
            </Link>
          </p>
        </>
      }
    >
      <form onSubmit={submit} className={forms.field} style={{ gap: 14 }}>
        <div className={forms.field}>
          <label className={forms.label} htmlFor="codigo">
            Código de 6 Dígitos
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
        {error && <div className={forms.error}>⚠ {error}</div>}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Validando…" : "Validar →"}
        </button>
      </form>
    </AuthShell>
  );
};
