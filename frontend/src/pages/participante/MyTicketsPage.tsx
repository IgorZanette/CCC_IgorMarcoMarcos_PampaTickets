import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { logout } from "../../api/auth";
import {
  listarMeusIngressos,
  type Ingresso,
} from "../../api/ingressos";
import { reembolsarPedido } from "../../api/pedidos";
import { Modal } from "../../components/Modal";
import { SkeletonGrid } from "../../components/Skeleton";
import { StatusPill } from "../../components/StatusPill";
import { initials, useCurrentUser } from "../../lib/auth-store";
import { extractErrorMessage } from "../../lib/errors";
import { dateFull } from "../../lib/format";
import { toastError, toastSuccess } from "../../lib/toast";

import styles from "./MyTicketsPage.module.css";

type Tab = "proximos" | "passados";

export const MyTicketsPage = () => {
  const [ingressos, setIngressos] = useState<Ingresso[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("proximos");
  // Ingresso cujo pedido está com o modal de reembolso aberto.
  const [reembolsoAlvo, setReembolsoAlvo] = useState<Ingresso | null>(null);
  // Pedidos com reembolso já solicitado nesta sessão — o status real do ingresso
  // só muda quando o webhook do Asaas confirmar o estorno (UC10/UC11).
  const [pedidosReembolsados, setPedidosReembolsados] = useState<Set<string>>(
    () => new Set(),
  );
  const user = useCurrentUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    listarMeusIngressos()
      .then((data) => {
        if (!cancelled) setIngressos(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar seus ingressos."));
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const memberSince = user
    ? new Date(user.criado_em).toLocaleDateString("pt-BR", {
        month: "short",
        year: "numeric",
      })
    : null;

  // Capturamos `agora` uma vez no mount — Date.now() em useMemo viola a regra
  // de pureza do react-hooks. Pra esta tela (estática durante a sessão) é ok.
  const [agora] = useState(() => Date.now());

  const buckets = useMemo(() => {
    if (!ingressos) return { proximos: [] as Ingresso[], passados: [] as Ingresso[] };
    const proximos: Ingresso[] = [];
    const passados: Ingresso[] = [];
    for (const ing of ingressos) {
      const futuro = new Date(ing.evento_data_inicio).getTime() > agora;
      if (ing.status === "ATIVO" && futuro) proximos.push(ing);
      else passados.push(ing);
    }
    return { proximos, passados };
  }, [ingressos, agora]);

  const tabCounts = {
    proximos: buckets.proximos.length,
    passados: buckets.passados.length,
  };

  const list = tab === "proximos" ? buckets.proximos : buckets.passados;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.avatar}>{user ? initials(user.nome) : "?"}</div>
        <div>
          <h1 className={styles.title}>
            Olá, {user ? user.nome.split(/\s+/)[0] : "visitante"} 👋
          </h1>
          <div className={styles.email}>
            {user
              ? `${user.email}${memberSince ? ` · Membro desde ${memberSince}` : ""}`
              : "Entre para acompanhar seus ingressos"}
          </div>
        </div>
        <div className={styles.headerActions}>
          {user ? (
            <button
              type="button"
              className={styles.secondary}
              onClick={handleLogout}
            >
              Sair
            </button>
          ) : (
            <Link to="/login" className={styles.secondary}>
              Entrar
            </Link>
          )}
        </div>
      </header>

      <div className={styles.tabs}>
        {(
          [
            { id: "proximos", l: "Próximos eventos" },
            { id: "passados", l: "Histórico" },
          ] as const
        ).map((t) => (
          <button
            type="button"
            key={t.id}
            className={styles.tab}
            data-active={tab === t.id ? "1" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.l}
            <span className={styles.tabCount}>{tabCounts[t.id]}</span>
          </button>
        ))}
      </div>

      <div className={styles.list}>
        {!user ? (
          <div className={styles.empty}>
            <Link to="/login" style={{ color: "var(--pt-accent)" }}>
              Entre na sua conta
            </Link>{" "}
            para ver seus ingressos.
          </div>
        ) : error ? (
          <div className={styles.empty}>{error}</div>
        ) : ingressos === null ? (
          <SkeletonGrid count={3} />
        ) : list.length === 0 ? (
          <div className={styles.empty}>
            Nenhum item nessa aba ainda. Que tal{" "}
            <Link to="/eventos" style={{ color: "var(--pt-accent)" }}>
              explorar eventos
            </Link>
            ?
          </div>
        ) : (
          list.map((ing) => (
            <IngressoRow
              key={ing.id}
              ing={ing}
              reembolsoSolicitado={
                ing.reembolso_solicitado ||
                (ing.pedido_id !== null &&
                  pedidosReembolsados.has(ing.pedido_id))
              }
              onReembolso={
                tab === "proximos" &&
                ing.pedido_id !== null &&
                !ing.reembolso_solicitado &&
                !pedidosReembolsados.has(ing.pedido_id)
                  ? () => setReembolsoAlvo(ing)
                  : undefined
              }
            />
          ))
        )}
      </div>

      <ReembolsoModal
        ing={reembolsoAlvo}
        onClose={() => setReembolsoAlvo(null)}
        onSuccess={(pedidoId) => {
          setPedidosReembolsados((prev) => new Set(prev).add(pedidoId));
          setReembolsoAlvo(null);
        }}
      />
    </div>
  );
};

const IngressoRow = ({
  ing,
  onReembolso,
  reembolsoSolicitado,
}: {
  ing: Ingresso;
  onReembolso?: () => void;
  reembolsoSolicitado: boolean;
}) => {
  const d = dateFull(ing.evento_data_inicio);
  const utilizado = ing.status === "UTILIZADO";
  const cancelado = ing.status === "CANCELADO";
  const pillStatus =
    cancelado ? "CANCELADO" : utilizado ? "PASSADO" : "CONFIRMADO";
  return (
    <div
      className={styles.row}
      style={{ opacity: utilizado || cancelado ? 0.7 : 1 }}
    >
      <div className={styles.rowCover}>
        <div className={styles.rowCoverOverlay} />
        <div className={styles.rowDate}>
          <div className={styles.rowMes}>{d.mes}</div>
          <div className={styles.rowDia}>{d.dia}</div>
        </div>
      </div>
      <div className={styles.rowBody}>
        <div className={styles.rowEyebrow}>
          <StatusPill status={pillStatus} />
        </div>
        <div className={styles.rowTitle}>{ing.evento_nome}</div>
        <div className={styles.rowMeta}>
          <span>
            📅 {d.semana}, {d.dia} {d.mes} · {d.hora}
          </span>
          <span>📍 {ing.evento_local}</span>
          <span>🎟 {ing.lote_nome}</span>
          <span className="pt-mono">#{ing.id.slice(0, 8)}</span>
        </div>
      </div>
      <div className={styles.rowActions}>
        {ing.pdf_url ? (
          <a
            href={ing.pdf_url}
            target="_blank"
            rel="noreferrer"
            className={styles.primary}
          >
            Baixar PDF
          </a>
        ) : (
          <span className={styles.ghost}>PDF em geração…</span>
        )}
        {utilizado && (
          ing.certificado_url ? (
            <a
              href={ing.certificado_url}
              target="_blank"
              rel="noreferrer"
              className={styles.secondary}
            >
              Baixar certificado
            </a>
          ) : (
            <span className={styles.ghost}>Certificado em geração…</span>
          )
        )}
        {reembolsoSolicitado ? (
          <span className={styles.refundPending}>
            ↩ Reembolso solicitado · aguardando confirmação
          </span>
        ) : (
          onReembolso && (
            <button type="button" className={styles.refund} onClick={onReembolso}>
              Solicitar reembolso
            </button>
          )
        )}
      </div>
    </div>
  );
};

// Modal de confirmação do reembolso (UC10). O reembolso é por pedido: cancela
// todos os ingressos da mesma compra e estorna pelo meio de pagamento original.
const ReembolsoModal = ({
  ing,
  onClose,
  onSuccess,
}: {
  ing: Ingresso | null;
  onClose: () => void;
  onSuccess: (pedidoId: string) => void;
}) => {
  const [motivo, setMotivo] = useState("");
  const [enviando, setEnviando] = useState(false);

  // Zera o motivo a cada novo alvo (padrão de ajuste durante o render), para
  // não vazar texto entre aberturas — o modal segue montado para animar a saída.
  const [alvoAnterior, setAlvoAnterior] = useState(ing?.id);
  if (ing?.id !== alvoAnterior) {
    setAlvoAnterior(ing?.id);
    setMotivo("");
  }

  const confirmar = async () => {
    if (!ing?.pedido_id || enviando) return;
    setEnviando(true);
    try {
      await reembolsarPedido(ing.pedido_id, { motivo: motivo.trim() || null });
      toastSuccess("Reembolso solicitado! Aguarde a confirmação do estorno.");
      onSuccess(ing.pedido_id);
    } catch (err) {
      toastError(err, "Não foi possível solicitar o reembolso.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal
      open={ing !== null}
      onClose={onClose}
      locked={enviando}
      labelledBy="reembolso-titulo"
    >
      <h2 id="reembolso-titulo" className={styles.modalTitle}>
        Solicitar reembolso
      </h2>
      <p className={styles.modalText}>
        O reembolso vale para o <strong>pedido inteiro</strong>: todos os
        ingressos comprados juntos para <strong>{ing?.evento_nome}</strong>{" "}
        serão cancelados e o valor devolvido pelo mesmo meio de pagamento. Essa
        ação não pode ser desfeita.
      </p>
      <label className={styles.modalLabel} htmlFor="reembolso-motivo">
        Motivo (opcional)
      </label>
      <textarea
        id="reembolso-motivo"
        className={styles.modalTextarea}
        value={motivo}
        onChange={(e) => setMotivo(e.target.value)}
        maxLength={500}
        placeholder="Conte para o organizador por que está pedindo o reembolso"
        disabled={enviando}
        autoFocus
      />
      <div className={styles.modalActions}>
        <button
          type="button"
          className={styles.secondary}
          onClick={onClose}
          disabled={enviando}
        >
          Voltar
        </button>
        <button
          type="button"
          className={styles.modalConfirm}
          onClick={confirmar}
          disabled={enviando}
        >
          {enviando ? "Enviando…" : "Confirmar reembolso"}
        </button>
      </div>
    </Modal>
  );
};
