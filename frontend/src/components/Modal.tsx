import { useEffect, useRef, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";

import styles from "./Modal.module.css";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  labelledBy?: string;
  // Trava o fechamento (ESC/clique no backdrop) — ex.: durante o envio de uma
  // requisição, para não desmontar o modal com a chamada em voo.
  locked?: boolean;
  // "md" (padrão, 440px) para confirmações; "lg" (640px) para formulários com
  // vários campos, evitando scroll desnecessário.
  size?: "md" | "lg";
};

// Modal genérico: overlay + card animados (fade no backdrop, scale+fade no card),
// com ESC e focus trap. O conteúdo (título, campos, ações) vem via children.
export const Modal = ({
  open,
  onClose,
  children,
  labelledBy,
  locked,
  size = "md",
}: ModalProps) => {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (!locked) onClose();
        return;
      }
      // Focus trap: mantém o Tab circulando dentro do dialog.
      if (e.key !== "Tab" || !dialogRef.current) return;
      const focusables = dialogRef.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]), textarea:not([disabled]), input:not([disabled]), a[href]",
      );
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      const dentro = dialogRef.current.contains(active);
      if (e.shiftKey && (active === first || !dentro)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (active === last || !dentro)) {
        e.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose, locked]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className={styles.overlay}
          role="presentation"
          onClick={() => {
            if (!locked) onClose();
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18, ease: "easeOut" }}
        >
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={labelledBy}
            className={styles.card}
            data-size={size}
            onClick={(e) => e.stopPropagation()}
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
