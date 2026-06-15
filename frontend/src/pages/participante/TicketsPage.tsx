import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { obterEvento, type Evento } from "../../api/eventos";
import { obterPedido, type Pedido } from "../../api/pedidos";
import { Icon } from "../../components/Icon";
import { LoadingBlock } from "../../components/Spinner";
import { extractErrorMessage } from "../../lib/errors";
import { dateLong, money } from "../../lib/format";

import styles from "./TicketsPage.module.css";

type LocationState = { pedidoId?: string; invoiceUrl?: string } | null;

export const TicketsPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const state = location.state as LocationState;
  const pedidoId = state?.pedidoId;
  const invoiceUrl = state?.invoiceUrl;

  const [ev, setEv] = useState<Evento | null>(null);
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!id) return;
    obterEvento(id).then(setEv).catch(() => undefined);
  }, [id]);

  useEffect(() => {
    if (!pedidoId) return;
    obterPedido(pedidoId)
      .then(setPedido)
      .catch((err) =>
        setError(extractErrorMessage(err, "Falha ao carregar o pedido.")),
      );
  }, [pedidoId]);

  const atualizar = async () => {
    if (!pedidoId) return;
    setRefreshing(true);
    try {
      setPedido(await obterPedido(pedidoId));
    } catch (err) {
      setError(extractErrorMessage(err, "Falha ao atualizar o pedido."));
    } finally {
      setRefreshing(false);
    }
  };

  if (!ev) return <LoadingBlock message="Carregando ingressos…" />;

  const status = pedido?.status;
  const pago = status === "PAGO";

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.checkmark}>
          <Icon name={pago ? "check" : "hourglass"} />
        </div>
        <h1 className={styles.title}>
          {pago ? "Pedido confirmado!" : "Pedido recebido"}
        </h1>
        <p className={styles.lead}>
          {pago
            ? "Seus ingressos foram emitidos e estão disponíveis em Meus ingressos."
            : "Estamos aguardando a confirmação do pagamento. Após a confirmação, seus ingressos aparecerão automaticamente em Meus ingressos."}
        </p>
      </header>

      <section className={styles.ticket}>
        <div className={styles.ticketBody}>
          <div className={styles.ticketDetails}>
            <div>
              <div className={styles.ticketLabel}>Evento</div>
              <div className={styles.ticketValue}>{ev.nome}</div>
            </div>
            <div>
              <div className={styles.ticketLabel}>Data</div>
              <div className={styles.ticketValue}>{dateLong(ev.data_inicio)}</div>
            </div>
            <div>
              <div className={styles.ticketLabel}>Local</div>
              <div className={styles.ticketValue}>{ev.local}</div>
            </div>
            {pedido && (
              <>
                <div>
                  <div className={styles.ticketLabel}>Status</div>
                  <div className={styles.ticketValue}>{pedido.status}</div>
                </div>
                <div>
                  <div className={styles.ticketLabel}>Total</div>
                  <div className={styles.ticketValue}>{money(pedido.valor_total)}</div>
                </div>
                <div>
                  <div className={styles.ticketLabel}>Pedido</div>
                  <div className={styles.ticketValue}>#{pedido.id.slice(0, 8)}</div>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {error && (
        <div className={styles.errorMsg}>
          <Icon name="warning" /> {error}
        </div>
      )}

      <div className={styles.actions}>
        {invoiceUrl && !pago && (
          <a
            href={invoiceUrl}
            target="_blank"
            rel="noreferrer"
            className={styles.secondary}
          >
            Abrir fatura
          </a>
        )}
        {pedidoId && !pago && (
          <button
            type="button"
            className={styles.secondary}
            onClick={atualizar}
            disabled={refreshing}
          >
            {refreshing ? "Atualizando…" : "Atualizar status"}
          </button>
        )}
        <Link to="/meus-ingressos" className={styles.primary}>
          Meus ingressos
        </Link>
      </div>
    </div>
  );
};
