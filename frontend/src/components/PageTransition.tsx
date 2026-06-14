import { type ReactNode } from "react";
import { motion } from "framer-motion";

// Transição leve de entrada de página (fade + slide sutil). Envolve o conteúdo
// renderizado pelo <Outlet> dos layouts. A `key` na rota faz o efeito reanimar
// a cada navegação.
export const PageTransition = ({ children }: { children: ReactNode }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
  >
    {children}
  </motion.div>
);
