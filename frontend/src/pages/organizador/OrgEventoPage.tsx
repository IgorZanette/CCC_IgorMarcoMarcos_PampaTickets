import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import {
  baixarRelatorio,
  cancelarEvento,
  encerrarEvento,
  gradientFor,
  obterResumoRelatorio,
  publicarEvento,
  type Evento,
  type RelatorioResumo,
} from "../../api/eventos";
import { MetricCard } from "../../components/MetricCard";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, money } from "../../lib/format";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";

import shared from "./shared.module.css";
import styles from "./OrgEventoPage.module.css";

export const OrgEventoPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento, loading, error: notFound } = useOutletContext<OrgOutlet>();

  const [current, setCurrent] = useState<Evento | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estado id-aware das métricas: carrega o id a que pertence, então a troca de evento
  // na navegação é resolvida por derivação no render (sem reset síncrono no effect).
  const [resumoState, setResumoState] = useState<{
    id: string;
    data: RelatorioResumo | null;
    error: string | null;
  } | null>(null);
  const [baixando, setBaixando] = useState(false);

  const ev = current ?? evento;

  const resumoAtual = id && resumoState?.id === id ? resumoState : null;
  const resumo = resumoAtual?.data ?? null;
  const resumoError = resumoAtual?.error ?? null;

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    obterResumoRelatorio(id)
      .then((data) => {
        if (!cancelled) setResumoState({ id, data, error: null });
      })
      .catch((err) => {
        if (!cancelled)
          setResumoState({
            id,
            data: null,
            error: extractErrorMessage(err, "Falha ao carregar métricas."),
          });
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading && !ev) return <div className={shared.body}>Carregando…</div>;

  if (!ev || notFound) {
    return (
      <div className={shared.body}>
        <div className={shared.cardPadded}>
          <h3 className={shared.cardTitle}>Evento não encontrado</h3>
          <p style={{ marginTop: 8, color: "var(--pt-org-text-dim)" }}>
            Este evento não existe ou você não tem acesso a ele.
          </p>
          <Link
            to="/organizador"
            className={shared.btnPrimary}
            style={{ marginTop: 16, display: "inline-block" }}
          >
            ← Todos os eventos
          </Link>
        </div>
      </div>
    );
  }

  const transicionar = async (acao: "publicar" | "encerrar" | "cancelar") => {
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

  const baixarPdf = async () => {
    setBaixando(true);
    try {
      await baixarRelatorio(ev.id);
    } catch (err) {
      const msg = extractErrorMessage(err, "Falha ao baixar o relatório.");
      // O botão de baixar só aparece com `resumo` carregado, então há estado do id atual.
      setResumoState((prev) => (prev ? { ...prev, error: msg } : prev));
    } finally {
      setBaixando(false);
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

        <div className={shared.cardPadded} style={{ marginBottom: 16 }}>
          <div className={styles.metricsHead}>
            <h3 className={shared.cardTitle}>Métricas e financeiro</h3>
            {resumo && (
              <button
                type="button"
                className={shared.btnSecondary}
                onClick={baixarPdf}
                disabled={baixando}
              >
                {baixando ? "Gerando…" : "Baixar relatório PDF"}
              </button>
            )}
          </div>

          {resumoError && (
            <div style={{ marginTop: 12, color: "var(--pt-org-text-dim)" }}>
              {resumoError}
            </div>
          )}
          {!resumoError && resumo === null && (
            <div style={{ marginTop: 12, color: "var(--pt-org-text-dim)" }}>
              Carregando métricas…
            </div>
          )}
          {resumo && (
            <div className={styles.metrics}>
              <MetricCard
                label="Receita líquida"
                value={money(resumo.receita_liquida)}
                tone="ok"
                sub={`Bruta: ${money(resumo.receita_bruta)}`}
              />
              <MetricCard
                label="Descontos (cupons)"
                value={money(resumo.desconto_cupons)}
                sub={`Reembolsos: ${money(resumo.valor_reembolsado)}`}
              />
              <MetricCard
                label="Ingressos vendidos"
                value={resumo.total_ingressos.toLocaleString("pt-BR")}
                sub={`Check-ins: ${resumo.total_checkins.toLocaleString("pt-BR")}`}
              />
              <MetricCard
                label="Comparecimento"
                value={`${(resumo.taxa_comparecimento * 100).toFixed(0)}%`}
              />
            </div>
          )}
        </div>

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

        <div className={styles.actions}>
          <Link to={`/organizador/eventos/${ev.id}/lotes`} className={shared.btnPrimary}>
            Gerenciar lotes & vendas →
          </Link>
          <Link to={`/organizador/eventos/${ev.id}/checkin`} className={shared.btnSecondary}>
            Iniciar check-in →
          </Link>
          <Link to={`/organizador/eventos/${ev.id}/participantes`} className={shared.btnSecondary}>
            Ver participantes →
          </Link>
          <Link to={`/organizador/eventos/${ev.id}/financeiro`} className={shared.btnSecondary}>
            Relatório financeiro →
          </Link>
        </div>
      </div>
    </>
  );
};
