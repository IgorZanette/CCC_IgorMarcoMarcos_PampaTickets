import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { buscarEnderecos, type GeoResult } from "../lib/geocode";
import { EventMap } from "./EventMap";
import styles from "./AddressAutocomplete.module.css";

export type EnderecoSelecionado = {
  local: string;
  endereco_completo: string;
  latitude: number;
  longitude: number;
};

type Props = {
  value: string;
  onChange: (texto: string) => void;
  onSelect: (selecionado: EnderecoSelecionado) => void;
  latitude?: number | null;
  longitude?: number | null;
  inputClassName?: string;
  placeholder?: string;
  required?: boolean;
};

// Campo de endereço com autocomplete via Nominatim e preview do mapa. Mantém o
// texto livre em `value` (compatível com o campo `local`); ao escolher uma
// sugestão, devolve também lat/lon e o endereço completo via onSelect.
export const AddressAutocomplete = ({
  value,
  onChange,
  onSelect,
  latitude,
  longitude,
  inputClassName,
  placeholder,
  required,
}: Props) => {
  const [sugestoes, setSugestoes] = useState<GeoResult[]>([]);
  const [aberto, setAberto] = useState(false);
  const [buscando, setBuscando] = useState(false);
  // Evita re-disparar a busca logo após o usuário escolher uma sugestão.
  const ignorarProxima = useRef(false);

  useEffect(() => {
    if (ignorarProxima.current) {
      ignorarProxima.current = false;
      return;
    }
    const termo = value.trim();
    const controller = new AbortController();
    // O setState fica dentro do timeout (não no corpo do effect) — atende à
    // regra do react-hooks e ainda debounce a busca por 500ms.
    const timer = setTimeout(() => {
      if (termo.length < 3) {
        setSugestoes([]);
        return;
      }
      setBuscando(true);
      buscarEnderecos(termo, controller.signal)
        .then((res) => {
          setSugestoes(res);
          setAberto(true);
        })
        .catch(() => undefined)
        .finally(() => setBuscando(false));
    }, 500);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value]);

  const escolher = (r: GeoResult) => {
    ignorarProxima.current = true;
    onChange(r.display_name);
    onSelect({
      local: r.display_name,
      endereco_completo: r.display_name,
      latitude: r.lat,
      longitude: r.lon,
    });
    setSugestoes([]);
    setAberto(false);
  };

  const temMapa = typeof latitude === "number" && typeof longitude === "number";

  return (
    <div className={styles.wrap}>
      <input
        className={inputClassName}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => sugestoes.length > 0 && setAberto(true)}
        onBlur={() => setTimeout(() => setAberto(false), 150)}
        placeholder={placeholder ?? "Digite o endereço do evento"}
        autoComplete="off"
        required={required}
      />

      <AnimatePresence>
        {aberto && sugestoes.length > 0 && (
          <motion.ul
            className={styles.suggestions}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
          >
            {sugestoes.map((s) => (
              <li key={s.place_id}>
                <button
                  type="button"
                  className={styles.option}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => escolher(s)}
                >
                  📍 {s.display_name}
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>

      {buscando && <div className={styles.hint}>Buscando endereços…</div>}

      {temMapa && (
        <div className={styles.mapWrap}>
          <EventMap lat={latitude!} lon={longitude!} height={180} />
          <a
            className={styles.mapLink}
            href={`https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=16/${latitude}/${longitude}`}
            target="_blank"
            rel="noreferrer"
          >
            Abrir no mapa ↗
          </a>
        </div>
      )}
    </div>
  );
};
