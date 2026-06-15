import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { cadastro, type Perfil } from "../../api/auth";
import { extractErrorMessage } from "../../lib/errors";
import { Icon } from "../../components/Icon";
import { AuthShell } from "./AuthShell";
import forms from "./forms.module.css";

export const CadastroPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const perfilInicial =
    (location.state as { perfil?: Perfil } | null)?.perfil ?? "PARTICIPANTE";
  const [perfil, setPerfil] = useState<Perfil>(perfilInicial);
  const [form, setForm] = useState({
    nome: "",
    email: "",
    cpf_cnpj: "",
    celular: "",
    senha: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((s) => ({ ...s, [k]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await cadastro({ ...form, perfil });
      navigate("/confirmar-email", { state: { email: form.email, senha: form.senha } });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Não foi possível criar a conta."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Criar conta"
      subtitle="Em alguns minutos você compra ingressos ou publica seu primeiro evento."
      footer={
        <>
          Já tem conta?{" "}
          <Link to="/login" style={{ color: "var(--pt-accent)", fontWeight: 600 }}>
            Entrar
          </Link>
        </>
      }
    >
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <div className={forms.label} style={{ marginBottom: 8 }}>
            Eu quero
          </div>
          <div className={forms.profile}>
            {(
              [
                {
                  v: "PARTICIPANTE",
                  l: "Comprar ingressos",
                  h: "Descobrir e participar de eventos",
                },
                {
                  v: "ORGANIZADOR",
                  l: "Vender ingressos",
                  h: "Publicar e gerenciar meus eventos",
                },
              ] as const
            ).map((opt) => (
              <button
                type="button"
                key={opt.v}
                className={forms.profileOption}
                data-active={perfil === opt.v ? "1" : undefined}
                onClick={() => setPerfil(opt.v)}
              >
                <div className={forms.profileLabel}>{opt.l}</div>
                <div className={forms.profileHint}>{opt.h}</div>
              </button>
            ))}
          </div>
        </div>

        <div className={forms.field}>
          <label className={forms.label}>Nome completo</label>
          <input className={forms.input} required value={form.nome} onChange={update("nome")} />
        </div>

        <div className={forms.field}>
          <label className={forms.label}>E-mail</label>
          <input
            type="email"
            className={forms.input}
            required
            value={form.email}
            onChange={update("email")}
          />
        </div>

        <div className={forms.row}>
          <div className={forms.field}>
            <label className={forms.label}>CPF / CNPJ</label>
            <input
              className={forms.input}
              required
              value={form.cpf_cnpj}
              onChange={update("cpf_cnpj")}
              placeholder="000.000.000-00"
            />
          </div>
          <div className={forms.field}>
            <label className={forms.label}>Celular</label>
            <input
              className={forms.input}
              required
              value={form.celular}
              onChange={update("celular")}
              placeholder="(00) 90000-0000"
            />
          </div>
        </div>

        <div className={forms.field}>
          <label className={forms.label}>Senha</label>
          <input
            type="password"
            className={forms.input}
            required
            minLength={8}
            value={form.senha}
            onChange={update("senha")}
            placeholder="Mínimo 8 caracteres"
          />
        </div>

        {error && (
          <div className={forms.error}>
            <Icon name="warning" /> {error}
          </div>
        )}
        <button type="submit" className={forms.primary} disabled={loading}>
          {loading ? "Criando…" : "Criar minha conta →"}
        </button>
      </form>
    </AuthShell>
  );
};
