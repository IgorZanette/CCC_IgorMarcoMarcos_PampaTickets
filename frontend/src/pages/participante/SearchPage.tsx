import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  cidadeFromLocal,
  gradientFor,
  listarEventos,
  type Evento,
} from "../../api/eventos";
import { extractErrorMessage } from "../../lib/errors";
import { dateFull } from "../../lib/format";

import styles from "./SearchPage.module.css";

export const SearchPage = () => {
  const [params, setParams] = useSearchParams();
  const [events, setEvents] = useState<Evento[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState(params.get("q") ?? "");
  const [city, setCity] = useState("Todas");
  const [sort, setSort] = useState<"Data" | "Nome">("Data");

  useEffect(() => {
    let cancelled = false;
    listarEventos()
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar eventos."));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const next = new URLSearchParams();
    if (q) next.set("q", q);
    setParams(next, { replace: true });
  }, [q, setParams]);

  const cities = useMemo(() => {
    if (!events) return ["Todas"];
    const set = new Set(events.map((e) => cidadeFromLocal(e.local)));
    return ["Todas", ...Array.from(set).sort()];
  }, [events]);

  const filtered = useMemo(() => {
    if (!events) return [];
    let list = events.filter((e) => {
      if (q && !e.nome.toLowerCase().includes(q.toLowerCase())) return false;
      if (city !== "Todas" && cidadeFromLocal(e.local) !== city) return false;
      return true;
    });
    if (sort === "Nome") list = [...list].sort((a, b) => a.nome.localeCompare(b.nome));
    if (sort === "Data")
      list = [...list].sort(
        (a, b) => new Date(a.data_inicio).getTime() - new Date(b.data_inicio).getTime(),
      );
    return list;
  }, [events, q, city, sort]);

  return (
    <div className={styles.page}>
      <div className={styles.searchBar}>
        <span className={styles.searchIcon}>⌕</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar evento, artista, local…"
          className={styles.searchInput}
        />
        <button className={styles.searchBtn}>Buscar</button>
      </div>

      <div className={styles.layout}>
        <aside className={styles.filters}>
          <div className={styles.filterGroup}>
            <div className={styles.filterLabel}>Cidade</div>
            <div className={styles.cityList}>
              {cities.map((c) => (
                <button
                  type="button"
                  key={c}
                  className={styles.cityRow}
                  data-active={city === c ? "1" : undefined}
                  onClick={() => setCity(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            className={styles.clearBtn}
            onClick={() => {
              setQ("");
              setCity("Todas");
            }}
          >
            Limpar filtros
          </button>
        </aside>

        <section>
          <div className={styles.resultsHead}>
            <div className={styles.resultsCount}>
              <strong>{filtered.length} eventos</strong>
              {city !== "Todas" && ` em ${city}`}
            </div>
            <div className={styles.sortGroup}>
              <span className={styles.sortLabel}>Ordenar por:</span>
              {(["Data", "Nome"] as const).map((s) => (
                <button
                  type="button"
                  key={s}
                  className={styles.sortBtn}
                  data-active={sort === s ? "1" : undefined}
                  onClick={() => setSort(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.grid}>
            {error ? (
              <div className={styles.empty}>{error}</div>
            ) : events === null ? (
              <div className={styles.empty}>Carregando eventos…</div>
            ) : filtered.length === 0 ? (
              <div className={styles.empty}>
                Nenhum evento encontrado com esses filtros.
              </div>
            ) : (
              filtered.map((e) => <ResultCard key={e.id} ev={e} />)
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

const ResultCard = ({ ev }: { ev: Evento }) => {
  const d = dateFull(ev.data_inicio);
  return (
    <Link to={`/eventos/${ev.id}`} className={styles.resultCard}>
      <div className={styles.resultCover} style={{ background: gradientFor(ev.id) }}>
        <div className={styles.resultDate}>
          <div className={styles.resultMes}>{d.mes}</div>
          <div className={styles.resultDia}>{d.dia}</div>
        </div>
      </div>
      <div className={styles.resultBody}>
        <div className={styles.resultTitle}>{ev.nome}</div>
        <div className={styles.resultMeta}>
          <span>📍 {cidadeFromLocal(ev.local)}</span>
          <span>
            {d.semana} · {d.hora}
          </span>
        </div>
      </div>
    </Link>
  );
};
