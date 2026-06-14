import { useEffect, useMemo, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import { realizarCheckin, type CheckinResponse } from "../../api/checkin";
import {
  listarIngressosDoEvento,
  type IngressoOrganizador,
} from "../../api/ingressos";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { toastError, toastSuccess } from "../../lib/toast";

import shared from "./shared.module.css";
import form from "./orgForms.module.css";
import styles from "./CheckinPage.module.css";

type StreamEntry = {
  id: number;
  ok: boolean;
  hash: string;
  message: string;
  at: string;
};

export const CheckinPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();

  const [ingressos, setIngressos] = useState<IngressoOrganizador[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busca, setBusca] = useState("");
  // Hash do ingresso em processo de check-in (trava só a linha clicada).
  const [checkingHash, setCheckingHash] = useState<string | null>(null);

  // Entrada manual (extra) por qr_code_hash.
  const [hash, setHash] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [stream, setStream] = useState<StreamEntry[]>([]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    listarIngressosDoEvento(id)
      .then((data) => {
        if (!cancelled) setIngressos(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar participantes."));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const filtrados = useMemo(() => {
    if (!ingressos) return null;
    const termo = busca.trim().toLowerCase();
    if (!termo) return ingressos;
    return ingressos.filter(
      (i) =>
        i.participante_nome.toLowerCase().includes(termo) ||
        i.participante_email.toLowerCase().includes(termo),
    );
  }, [ingressos, busca]);

  const totais = useMemo(() => {
    if (!ingressos) return { total: 0, presentes: 0 };
    return {
      total: ingressos.length,
      presentes: ingressos.filter((i) => i.status === "UTILIZADO").length,
    };
  }, [ingressos]);

  const registrarStream = (entry: Omit<StreamEntry, "id">) =>
    setStream((prev) => [{ ...entry, id: Date.now() }, ...prev].slice(0, 20));

  // Marca o ingresso como utilizado na lista local após o check-in confirmado.
  const marcarUtilizado = (qrHash: string) =>
    setIngressos((prev) =>
      prev
        ? prev.map((i) =>
            i.qr_code_hash === qrHash ? { ...i, status: "UTILIZADO" } : i,
          )
        : prev,
    );

  // Check-in direto pela lista (1 clique, sem copiar/colar o hash).
  const checkinPelaLista = async (ingresso: IngressoOrganizador) => {
    setCheckingHash(ingresso.qr_code_hash);
    try {
      const res = await realizarCheckin({ qr_code_hash: ingresso.qr_code_hash });
      marcarUtilizado(ingresso.qr_code_hash);
      registrarStream({
        ok: true,
        hash: ingresso.qr_code_hash,
        message: `${ingresso.participante_nome} • check-in OK`,
        at: new Date(res.realizado_em).toLocaleTimeString("pt-BR"),
      });
      toastSuccess(`Check-in de ${ingresso.participante_nome} realizado!`);
    } catch (err) {
      const msg = extractErrorMessage(err, "Falha ao validar ingresso.");
      registrarStream({
        ok: false,
        hash: ingresso.qr_code_hash,
        message: `${ingresso.participante_nome} • ${msg}`,
        at: new Date().toLocaleTimeString("pt-BR"),
      });
      toastError(msg);
    } finally {
      setCheckingHash(null);
    }
  };

  // Entrada manual (extra) — útil quando a leitura vem da câmera/QR.
  const validarManual = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = hash.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      const res: CheckinResponse = await realizarCheckin({ qr_code_hash: trimmed });
      marcarUtilizado(trimmed);
      registrarStream({
        ok: true,
        hash: trimmed,
        message: `${res.participante_nome} • check-in OK`,
        at: new Date(res.realizado_em).toLocaleTimeString("pt-BR"),
      });
      toastSuccess("Check-in realizado!");
      setHash("");
    } catch (err) {
      const msg = extractErrorMessage(err, "Falha ao validar ingresso.");
      registrarStream({
        ok: false,
        hash: trimmed,
        message: msg,
        at: new Date().toLocaleTimeString("pt-BR"),
      });
      toastError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Check-in ao vivo`}
        title="Check-in ao vivo"
        actions={<StatusPill status="AO VIVO" pulse />}
      />

      <div className={shared.body}>
        {error && (
          <div
            className={shared.cardPadded}
            style={{ borderColor: "var(--pt-danger)", color: "var(--pt-danger)" }}
          >
            ⚠ {error}
          </div>
        )}

        {/* Lista de participantes com check-in de 1 clique */}
        <div className={shared.card}>
          <div className={shared.tableHead}>
            <h3 className={shared.cardTitle}>Participantes</h3>
            <span className={styles.streamMeta}>
              {totais.presentes}/{totais.total} presentes
            </span>
          </div>

          {ingressos !== null && ingressos.length > 0 && (
            <div style={{ padding: "12px 24px 0" }}>
              <input
                className={form.input}
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar por nome ou e-mail…"
                style={{ maxWidth: 360 }}
              />
            </div>
          )}

          {filtrados === null ? (
            <div className={styles.loadingBox}>Carregando participantes…</div>
          ) : ingressos !== null && ingressos.length === 0 ? (
            <EmptyState
              icon="🎫"
              title="Nenhum ingresso vendido ainda"
              hint="Quando houver vendas, os participantes aparecerão aqui para check-in."
            />
          ) : filtrados.length === 0 ? (
            <EmptyState
              icon="🔍"
              title="Nenhum participante encontrado"
              hint={`Não há resultados para "${busca}".`}
            />
          ) : (
            <table className={shared.table}>
              <thead>
                <tr>
                  <th>Participante</th>
                  <th>Lote</th>
                  <th>Status</th>
                  <th className={styles.actionCol} />
                </tr>
              </thead>
              <tbody>
                {filtrados.map((i) => {
                  const jaUsado = i.status === "UTILIZADO";
                  const cancelado = i.status === "CANCELADO";
                  return (
                    <tr key={i.id}>
                      <td>
                        <div className={styles.attendeeName}>
                          {i.participante_nome}
                        </div>
                        <div className={styles.attendeeMail}>
                          {i.participante_email}
                        </div>
                      </td>
                      <td>
                        <span className={styles.loteTag}>{i.lote_nome}</span>
                      </td>
                      <td>
                        <StatusPill
                          status={
                            jaUsado
                              ? "PRESENTE"
                              : cancelado
                                ? "CANCELADO"
                                : "PENDENTE"
                          }
                        />
                      </td>
                      <td className={styles.actionCol}>
                        <button
                          className={shared.btnPrimary}
                          onClick={() => checkinPelaLista(i)}
                          disabled={
                            jaUsado ||
                            cancelado ||
                            checkingHash === i.qr_code_hash
                          }
                        >
                          {checkingHash === i.qr_code_hash
                            ? "Validando…"
                            : jaUsado
                              ? "✓ Presente"
                              : "Check-in"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Entrada manual (extra) + stream */}
        <div className={styles.charts}>
          <div className={shared.cardPadded}>
            <h3 className={shared.cardTitle}>Validar por código (extra)</h3>
            <p style={{ color: "var(--pt-text-dim)", fontSize: 13, marginTop: 6 }}>
              Cole o <code>qr_code_hash</code> do ingresso — útil quando a leitura
              vem da câmera lendo o QR Code.
            </p>
            <form
              onSubmit={validarManual}
              style={{ marginTop: 14, display: "flex", gap: 8 }}
            >
              <input
                type="text"
                className={form.input}
                value={hash}
                onChange={(e) => setHash(e.target.value)}
                placeholder="qr_code_hash"
                style={{ flex: 1, fontFamily: "var(--pt-font-mono)" }}
              />
              <button
                type="submit"
                className={shared.btnPrimary}
                disabled={submitting || !hash.trim()}
              >
                {submitting ? "Validando…" : "Validar"}
              </button>
            </form>
          </div>

          <div className={shared.card}>
            <div className={shared.tableHead}>
              <h3 className={shared.cardTitle}>Stream de check-ins</h3>
              <span className={styles.streamMeta}>{stream.length} recentes</span>
            </div>
            <div>
              {stream.length === 0 ? (
                <div className={styles.loadingBox}>
                  Nenhum check-in nesta sessão ainda.
                </div>
              ) : (
                stream.map((p, i) => (
                  <div
                    key={p.id}
                    className={styles.streamRow}
                    style={
                      i > 0
                        ? { borderTop: "1px solid var(--pt-border)" }
                        : undefined
                    }
                  >
                    <div
                      className={styles.streamMark}
                      data-ok={p.ok ? "1" : undefined}
                    >
                      {p.ok ? "✓" : "✗"}
                    </div>
                    <div className={styles.streamInfo}>
                      <div className={styles.streamName}>{p.message}</div>
                      <div
                        className={`${styles.streamSub} pt-mono`}
                        style={{ fontSize: 11 }}
                      >
                        {p.hash.slice(0, 32)}
                        {p.hash.length > 32 ? "…" : ""}
                      </div>
                    </div>
                    <div className={`${styles.streamTime} pt-mono`}>{p.at}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
