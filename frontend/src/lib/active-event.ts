// Hidratação do evento do organizador a partir do id da rota (/organizador/eventos/:id).
// A fonte da verdade é a URL — não há mais "evento ativo" em localStorage.

import { useEffect, useState } from "react";

import { obterEventoOrganizador, type Evento } from "../api/eventos";

// O resultado carrega o `id` a que pertence — assim a staleness (resultado de um id
// anterior durante a navegação) vira derivação no render, sem precisar resetar estado
// dentro do effect (que dispara re-renders em cascata; ver react-hooks/set-state-in-effect).
type EventoState = { id: string; evento: Evento | null; error: boolean };

export const useEvento = (id: string | null | undefined) => {
  const [state, setState] = useState<EventoState | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    obterEventoOrganizador(id)
      .then((data) => {
        if (!cancelled) setState({ id, evento: data, error: false });
      })
      .catch(() => {
        if (!cancelled) setState({ id, evento: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Só consideramos o estado se ele for do id atual; senão ainda está carregando.
  const fresh = id && state?.id === id ? state : null;
  return {
    evento: fresh?.evento ?? null,
    loading: id != null && fresh === null,
    error: fresh?.error ?? false,
  };
};
