import { useState, type ReactNode } from "react";

import { Modal } from "./Modal";
import { toastError } from "../lib/toast";
import styles from "./ConfirmDialog.module.css";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => Promise<void> | void;
  onClose: () => void;
};

// Diálogo de confirmação animado (sobre o Modal) — substitui o confirm()
// nativo do navegador. O onConfirm faz a ação; se lançar, mostramos toast de
// erro e mantemos o diálogo aberto.
export const ConfirmDialog = ({
  open,
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  danger,
  onConfirm,
  onClose,
}: ConfirmDialogProps) => {
  const [loading, setLoading] = useState(false);

  const confirmar = async () => {
    setLoading(true);
    try {
      await onConfirm();
      onClose();
    } catch (err) {
      toastError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} locked={loading} labelledBy="confirm-titulo">
      <h2 id="confirm-titulo" className={styles.title}>
        {title}
      </h2>
      <div className={styles.message}>{message}</div>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.cancel}
          onClick={onClose}
          disabled={loading}
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          className={styles.confirm}
          data-danger={danger ? "1" : undefined}
          onClick={confirmar}
          disabled={loading}
        >
          {loading ? "Processando…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
};
