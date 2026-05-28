import { useState } from "react";

import { realizarCheckin, type CheckinResponse } from "../../api/checkin";
import { PageHeader } from "../../components/PageHeader";
import { StatusPill } from "../../components/StatusPill";
import { useActiveEvent } from "../../lib/active-event";
import { extractErrorMessage } from "../../lib/errors";

import shared from "./shared.module.css";
import styles from "./CheckinPage.module.css";

type StreamEntry = {
  id: number;
  ok: boolean;
  hash: string;
  message: string;
  at: string;
};

export const CheckinPage = () => {
  const { evento } = useActiveEvent();
  const [hash, setHash] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [stream, setStream] = useState<StreamEntry[]>([]);

  const validar = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = hash.trim();
    if (!trimmed) return;
    setSubmitting(true);
    let entry: StreamEntry;
    try {
      const res: CheckinResponse = await realizarCheckin({ qr_code_hash: trimmed });
      entry = {
        id: Date.now(),
        ok: true,
        hash: trimmed,
        message: `Ingresso #${res.ingresso_id.slice(0, 8)} validado`,
        at: new Date(res.realizado_em).toLocaleTimeString("pt-BR"),
      };
    } catch (err) {
      entry = {
        id: Date.now(),
        ok: false,
        hash: trimmed,
        message: extractErrorMessage(err, "Falha ao validar ingresso."),
        at: new Date().toLocaleTimeString("pt-BR"),
      };
    }
    setStream((prev) => [entry, ...prev].slice(0, 20));
    setHash("");
    setSubmitting(false);
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Check-in ao vivo`}
        title="Check-in ao vivo"
        actions={<StatusPill status="AO VIVO" pulse />}
      />

      <div className={shared.body}>
        {!evento && (
          <div
            className={shared.cardPadded}
            style={{ marginBottom: 16, color: "var(--pt-org-text-dim)" }}
          >
            Selecione um evento no painel para destacar o contexto. O check-in
            valida via QR code e a posse do evento é checada no backend.
          </div>
        )}

        <div className={styles.charts}>
          <div className={shared.cardPadded}>
            <h3 className={shared.cardTitle}>Validar ingresso</h3>
            <p style={{ color: "var(--pt-org-text-dim)", fontSize: 13, marginTop: 6 }}>
              Cole o <code>qr_code_hash</code> do ingresso. Em produção, isso
              vem da câmera lendo o QR Code.
            </p>
            <form onSubmit={validar} style={{ marginTop: 14, display: "flex", gap: 8 }}>
              <input
                type="text"
                value={hash}
                onChange={(e) => setHash(e.target.value)}
                placeholder="qr_code_hash"
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  border: "1px solid var(--pt-org-border)",
                  borderRadius: 6,
                  fontFamily: "ui-monospace, monospace",
                  fontSize: 13,
                }}
                autoFocus
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
                <div
                  style={{
                    padding: 24,
                    textAlign: "center",
                    color: "var(--pt-org-text-dim)",
                    fontSize: 13,
                  }}
                >
                  Nenhum check-in nesta sessão ainda.
                </div>
              ) : (
                stream.map((p, i) => (
                  <div
                    key={p.id}
                    className={styles.streamRow}
                    style={
                      i > 0 ? { borderTop: "1px solid var(--pt-org-border)" } : undefined
                    }
                  >
                    <div className={styles.streamMark} data-ok={p.ok ? "1" : undefined}>
                      {p.ok ? "✓" : "✗"}
                    </div>
                    <div className={styles.streamInfo}>
                      <div className={styles.streamName}>{p.message}</div>
                      <div className={`${styles.streamSub} pt-mono`} style={{ fontSize: 11 }}>
                        {p.hash.slice(0, 32)}{p.hash.length > 32 ? "…" : ""}
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
