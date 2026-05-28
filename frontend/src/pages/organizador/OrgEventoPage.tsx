import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  cancelarEvento,
  encerrarEvento,
  gradientFor,
  publicarEvento,
  type Evento,
} from "../../api/eventos";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import { useActiveEvent } from "../../lib/active-event";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong } from "../../lib/format";

import shared from "./shared.module.css";
import styles from "./OrgEventoPage.module.css";

export const OrgEventoPage = () => {
  const navigate = useNavigate();
  const { evento, loading } = useActiveEvent();
  const [current, setCurrent] = useState<Evento | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ev = current ?? evento;

  if (loading && !ev) return <div className={shared.body}>Carregando…</div>;

  if (!ev) {
    return (
      <div className={shared.body}>
        <div className={shared.cardPadded}>
          <h3 className={shared.cardTitle}>Nenhum evento selecionado</h3>
          <p style={{ marginTop: 8, color: "var(--pt-org-text-dim)" }}>
            Volte para o painel e escolha um evento para gerenciar.
          </p>
          <Link
            to="/organizador"
            className={shared.btnPrimary}
            style={{ marginTop: 16, display: "inline-block" }}
          >
            Ir para o painel →
          </Link>
        </div>
      </div>
    );
  }

  const transicionar = async (acao: "publicar" | "encerrar" | "cancelar") => {
    if (!ev) return;
    setBusy(true);
    setError(null);
    try {
      const fn =
        acao === "publicar"
          ? publicarEvento
          : acao === "encerrar"
            ? encerrarEvento
            : cancelarEvento;
      setCurrent(await fn(ev.id));
    } catch (err) {
      setError(extractErrorMessage(err, `Falha ao ${acao} o evento.`));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb={`Eventos / ${ev.nome}`}
        title={ev.nome}
        actions={
          <>
            <StatusPill status={ev.status} />
            {ev.status === "RASCUNHO" && (
              <button
                className={shared.btnPrimary}
                onClick={() => transicionar("publicar")}
                disabled={busy}
              >
                Publicar
              </button>
            )}
            {ev.status === "PUBLICADO" && (
              <button
                className={shared.btnSecondary}
                onClick={() => transicionar("encerrar")}
                disabled={busy}
              >
                Encerrar
              </button>
            )}
            {(ev.status === "RASCUNHO" || ev.status === "PUBLICADO") && (
              <button
                className={shared.btnDark}
                onClick={() => transicionar("cancelar")}
                disabled={busy}
              >
                Cancelar evento
              </button>
            )}
            <button
              className={shared.btnSecondary}
              onClick={() => navigate("/organizador/eventos/novo")}
            >
              + Novo evento
            </button>
          </>
        }
      />

      <div className={shared.body}>
        {error && (
          <div
            className={shared.cardPadded}
            style={{ borderColor: "#c8102e", color: "#c8102e", marginBottom: 16 }}
          >
            ⚠ {error}
          </div>
        )}

        <div className={styles.layout}>
          <div className={shared.card}>
            <div className={styles.cover} style={{ background: gradientFor(ev.id) }} />
            <div className={styles.coverInfo}>
              <div className={styles.metaGrid}>
                <div>
                  <div className={shared.eyebrow}>Início</div>
                  <div className={styles.metaValue}>{dateLong(ev.data_inicio)}</div>
                </div>
                <div>
                  <div className={shared.eyebrow}>Encerramento</div>
                  <div className={styles.metaValue}>{dateLong(ev.data_fim)}</div>
                </div>
                <div>
                  <div className={shared.eyebrow}>Local</div>
                  <div className={styles.metaValue}>{ev.local}</div>
                </div>
              </div>
              <div className={styles.descBlock}>
                <div className={shared.eyebrow}>Descrição</div>
                <p className={styles.desc}>
                  {ev.descricao ?? "Sem descrição cadastrada."}
                </p>
              </div>
            </div>
          </div>

          <div className={styles.aside}>
            <div className={shared.cardPadded}>
              <h3 className={shared.cardTitle}>Próximas ações</h3>
              <p style={{ marginTop: 8, color: "var(--pt-org-text-dim)", fontSize: 13 }}>
                Use os atalhos abaixo para gerenciar os lotes, fazer check-in
                ao vivo ou acompanhar participantes.
              </p>
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Link to="/organizador/lotes" className={shared.btnPrimary}>
            Gerenciar lotes & vendas →
          </Link>
          <Link to="/organizador/checkin" className={shared.btnSecondary}>
            Iniciar check-in →
          </Link>
          <Link to="/organizador/participantes" className={shared.btnSecondary}>
            Ver participantes →
          </Link>
        </div>
      </div>
    </>
  );
};
