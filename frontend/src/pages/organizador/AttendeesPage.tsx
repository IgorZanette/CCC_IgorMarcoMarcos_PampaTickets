import { useEffect, useMemo, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import {
  listarIngressosDoEvento,
  type IngressoOrganizador,
} from "../../api/ingressos";
import { Icon } from "../../components/Icon";
import { PageHeader } from "../../components/PageHeader";
import { LoadingBlock } from "../../components/Spinner";
import { StatusPill } from "../../components/StatusPill";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong } from "../../lib/format";

import shared from "./shared.module.css";
import styles from "./orgForms.module.css";

export const AttendeesPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();
  const [ingressos, setIngressos] = useState<IngressoOrganizador[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busca, setBusca] = useState("");

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

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Participantes`}
        title="Participantes"
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

        {ingressos !== null && ingressos.length > 0 && (
          <input
            className={`${styles.input} ${styles.searchInput}`}
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por nome ou e-mail…"
          />
        )}

        <div className={shared.card}>
          {filtrados === null ? (
            <LoadingBlock message="Carregando participantes…" />
          ) : ingressos !== null && ingressos.length === 0 ? (
            <div className={styles.empty}>
              Nenhum ingresso vendido para este evento ainda.
            </div>
          ) : filtrados.length === 0 ? (
            <div className={styles.empty}>
              Nenhum participante encontrado para "{busca}".
            </div>
          ) : (
            <table className={shared.table}>
              <thead>
                <tr>
                  <th>Participante</th>
                  <th>Lote</th>
                  <th>QR Code</th>
                  <th>Status</th>
                  <th>Emitido em</th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((i) => (
                  <tr key={i.id}>
                    <td>
                      <div className={styles.bold}>{i.participante_nome}</div>
                      <div className={styles.dim}>{i.participante_email}</div>
                    </td>
                    <td>
                      <span className={styles.tipo}>{i.lote_nome}</span>
                    </td>
                    <td
                      className={styles.dim}
                      style={{
                        fontFamily: "var(--pt-font-mono)",
                        fontSize: 11,
                        wordBreak: "break-all",
                        maxWidth: 220,
                      }}
                      title={i.qr_code_hash}
                    >
                      {i.qr_code_hash}
                    </td>
                    <td>
                      <StatusPill status={i.status} />
                    </td>
                    <td className={styles.dim}>{dateLong(i.emitido_em)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
};
