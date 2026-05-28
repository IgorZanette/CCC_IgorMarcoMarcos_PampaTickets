// Seletor mínimo de "evento ativo do organizador". Persiste o id em localStorage
// e hidrata o Evento completo via API. Vale como atalho enquanto as rotas do
// organizador são singulares (/organizador/lotes etc.); some quando migrar para
// /organizador/eventos/:id/...

import { useEffect, useState } from "react";

import { obterEventoOrganizador, type Evento } from "../api/eventos";

const KEY = "pt_org_active_event";
const CHANGE_EVENT = "pt-active-event-change";

export const getActiveEventId = (): string | null => localStorage.getItem(KEY);

export const setActiveEventId = (id: string | null) => {
  if (id) localStorage.setItem(KEY, id);
  else localStorage.removeItem(KEY);
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
};

export const useActiveEvent = () => {
  const [id, setId] = useState<string | null>(() => getActiveEventId());
  const [evento, setEvento] = useState<Evento | null>(null);

  useEffect(() => {
    const sync = () => setId(getActiveEventId());
    window.addEventListener(CHANGE_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(CHANGE_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    obterEventoOrganizador(id)
      .then((data) => {
        if (!cancelled) setEvento(data);
      })
      .catch(() => {
        if (!cancelled) setEvento(null);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Quando o id volta a ser null (deselecionado), descartamos o evento antigo
  // em vez de guardar em state — evita setState dentro do effect.
  // `loading` é derivado: temos id mas ainda não temos o evento hidratado.
  const visible = id ? evento : null;
  return {
    evento: visible,
    loading: id != null && evento?.id !== id,
    setActiveEventId,
  };
};
