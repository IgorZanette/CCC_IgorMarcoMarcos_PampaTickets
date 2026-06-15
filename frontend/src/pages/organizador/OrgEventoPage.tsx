import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import {
  baixarRelatorio,
  cancelarEvento,
  editarEvento,
  encerrarEvento,
  gradientFor,
  obterResumoRelatorio,
  publicarEvento,
  type Evento,
  type RelatorioResumo,
} from "../../api/eventos";
import { AddressAutocomplete } from "../../components/AddressAutocomplete";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { EventMap } from "../../components/EventMap";
import { Icon } from "../../components/Icon";
import { MetricCard } from "../../components/MetricCard";
import { PageHeader } from "../../components/PageHeader";
import { LoadingBlock, Spinner } from "../../components/Spinner";
import { StatusPill } from "../../components/StatusPill";
import { extractErrorMessage } from "../../lib/errors";
import { toastSuccess } from "../../lib/toast";
import { dateLong, localToUtcIso, money, utcIsoToLocalInput } from "../../lib/format";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";

import shared from "./shared.module.css";
import styles from "./OrgEventoPage.module.css";
import form from "./CreateEventPage.module.css";

export const OrgEventoPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento, loading, error: notFound } = useOutletContext<OrgOutlet>();

  const [current, setCurrent] = useState<Evento | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<null | "publicar" | "encerrar" | "cancelar">(null);

  // Edição inline do evento (UC02). Só permitida em RASCUNHO/PUBLICADO — mesma
  // regra do backend (`_STATUS_EDITAVEIS`); o botão nem aparece nos demais.
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [dados, setDados] = useState({
    nome: "",
    descricao: "",
    dataInicio: "",
    dataFim: "",
    local: "",
    enderecoCompleto: null as string | null,
    latitude: null as number | null,
    longitude: null as number | null,
  });

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

  if (loading && !ev)
    return (
      <div className={shared.body}>
        <LoadingBlock message="Carregando evento…" />
      </div>
    );

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

  const editavel = ev.status === "RASCUNHO" || ev.status === "PUBLICADO";

  const iniciarEdicao = () => {
    setDados({
      nome: ev.nome,
      descricao: ev.descricao ?? "",
      dataInicio: utcIsoToLocalInput(ev.data_inicio),
      dataFim: utcIsoToLocalInput(ev.data_fim),
      local: ev.local,
      enderecoCompleto: ev.endereco_completo,
      latitude: ev.latitude,
      longitude: ev.longitude,
    });
    setEditError(null);
    setEditing(true);
  };

  const salvarEdicao = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setEditError(null);
    try {
      const atualizado = await editarEvento(ev.id, {
        nome: dados.nome,
        descricao: dados.descricao || null,
        data_inicio: localToUtcIso(dados.dataInicio),
        data_fim: localToUtcIso(dados.dataFim),
        local: dados.local,
        endereco_completo: dados.enderecoCompleto,
        latitude: dados.latitude,
        longitude: dados.longitude,
      });
      setCurrent(atualizado);
      setEditing(false);
      toastSuccess("Evento atualizado!");
    } catch (err) {
      setEditError(extractErrorMessage(err, "Falha ao salvar o evento."));
    } finally {
      setSaving(false);
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
            {!editing && editavel && (
              <button
                className={shared.btnSecondary}
                onClick={iniciarEdicao}
                disabled={busy}
              >
                Editar
              </button>
            )}
            {!editing && ev.status === "RASCUNHO" && (
              <button
                className={shared.btnPrimary}
                onClick={() => setConfirm("publicar")}
                disabled={busy}
              >
                Publicar
              </button>
            )}
            {!editing && ev.status === "PUBLICADO" && (
              <button
                className={shared.btnSecondary}
                onClick={() => setConfirm("encerrar")}
                disabled={busy}
              >
                Encerrar
              </button>
            )}
            {!editing && editavel && (
              <button
                className={shared.btnDark}
                onClick={() => setConfirm("cancelar")}
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
            <Icon name="warning" /> {error}
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
            <div
              style={{
                marginTop: 12,
                color: "var(--pt-org-text-dim)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Spinner size={18} /> Carregando métricas…
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

        {editing ? (
          <form className={shared.cardPadded} onSubmit={salvarEdicao}>
            <h3 className={shared.cardTitle}>Editar evento</h3>
            <p className={form.lead} style={{ marginTop: 4 }}>
              As alterações ficam visíveis imediatamente. Só é possível editar
              eventos em <strong>RASCUNHO</strong> ou <strong>PUBLICADO</strong>.
            </p>

            <div className={form.field}>
              <label className={form.fieldLabel}>Nome do evento *</label>
              <input
                className={form.input}
                value={dados.nome}
                onChange={(e) => setDados({ ...dados, nome: e.target.value })}
                required
                minLength={3}
                maxLength={255}
              />
            </div>

            <div className={form.field}>
              <label className={form.fieldLabel}>Descrição</label>
              <textarea
                className={form.textarea}
                rows={4}
                value={dados.descricao}
                onChange={(e) => setDados({ ...dados, descricao: e.target.value })}
                placeholder="Conte o que torna esse evento único…"
              />
            </div>

            <div className={form.row}>
              <div className={form.field}>
                <label className={form.fieldLabel}>Início *</label>
                <input
                  type="datetime-local"
                  className={form.input}
                  value={dados.dataInicio}
                  onChange={(e) =>
                    setDados({ ...dados, dataInicio: e.target.value })
                  }
                  required
                />
              </div>
              <div className={form.field}>
                <label className={form.fieldLabel}>Encerramento *</label>
                <input
                  type="datetime-local"
                  className={form.input}
                  value={dados.dataFim}
                  onChange={(e) =>
                    setDados({ ...dados, dataFim: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <div className={form.field}>
              <label className={form.fieldLabel}>Local *</label>
              <AddressAutocomplete
                value={dados.local}
                onChange={(texto) =>
                  setDados({
                    ...dados,
                    local: texto,
                    latitude: null,
                    longitude: null,
                    enderecoCompleto: null,
                  })
                }
                onSelect={(sel) =>
                  setDados({
                    ...dados,
                    local: sel.local,
                    enderecoCompleto: sel.endereco_completo,
                    latitude: sel.latitude,
                    longitude: sel.longitude,
                  })
                }
                latitude={dados.latitude}
                longitude={dados.longitude}
                inputClassName={form.input}
                required
              />
            </div>

            {editError && (
              <div
                style={{
                  marginTop: 12,
                  padding: "10px 12px",
                  background: "rgba(200, 16, 46, 0.08)",
                  color: "#c8102e",
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                <Icon name="warning" /> {editError}
              </div>
            )}

            <div className={form.formActions}>
              <button
                type="button"
                className={shared.btnSecondary}
                onClick={() => setEditing(false)}
                disabled={saving}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className={shared.btnPrimary}
                disabled={saving}
              >
                {saving ? "Salvando…" : "Salvar alterações"}
              </button>
            </div>
          </form>
        ) : (
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
              {ev.latitude != null && ev.longitude != null && (
                <div style={{ marginTop: 16 }}>
                  <EventMap lat={ev.latitude} lon={ev.longitude} height={200} />
                </div>
              )}
              <div className={styles.descBlock}>
                <div className={shared.eyebrow}>Descrição</div>
                <p className={styles.desc}>
                  {ev.descricao ?? "Sem descrição cadastrada."}
                </p>
              </div>
            </div>
          </div>
        )}

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
      <ConfirmDialog
        open={confirm === "publicar"}
        title="Publicar evento?"
        message="O evento ficará visível ao público e os participantes poderão comprar ingressos. Deseja continuar?"
        confirmLabel="Publicar"
        onConfirm={() => transicionar("publicar")}
        onClose={() => setConfirm(null)}
      />

      <ConfirmDialog
        open={confirm === "encerrar"}
        title="Encerrar evento?"
        message="O evento será marcado como encerrado. Não será mais possível vender ingressos."
        confirmLabel="Encerrar"
        onConfirm={() => transicionar("encerrar")}
        onClose={() => setConfirm(null)}
      />

      <ConfirmDialog
        open={confirm === "cancelar"}
        title="Cancelar evento?"
        message="Esta ação não pode ser desfeita. O evento será cancelado e sairá de circulação."
        confirmLabel="Cancelar evento"
        danger
        onConfirm={() => transicionar("cancelar")}
        onClose={() => setConfirm(null)}
      />
    </>
  );
};
