// Busca de endereços via Nominatim (OpenStreetMap) — gratuito, sem API key.
// Policy do serviço: máx ~1 req/s (garantido pelo debounce no componente) e um
// Referer/User-Agent identificando a app (o browser envia o Referer sozinho).

export type GeoResult = {
  display_name: string;
  lat: number;
  lon: number;
  place_id: number;
};

const NOMINATIM = "https://nominatim.openstreetmap.org/search";

export const buscarEnderecos = async (
  query: string,
  signal?: AbortSignal,
): Promise<GeoResult[]> => {
  if (query.trim().length < 3) return [];
  const url = new URL(NOMINATIM);
  url.searchParams.set("format", "json");
  url.searchParams.set("q", query);
  url.searchParams.set("limit", "5");
  url.searchParams.set("countrycodes", "br"); // foco no Brasil
  const res = await fetch(url.toString(), {
    signal,
    headers: { "Accept-Language": "pt-BR" },
  });
  if (!res.ok) throw new Error("Falha na busca de endereço");
  const data = (await res.json()) as Array<{
    display_name: string;
    lat: string;
    lon: string;
    place_id: number;
  }>;
  return data.map((d) => ({
    display_name: d.display_name,
    lat: parseFloat(d.lat),
    lon: parseFloat(d.lon),
    place_id: d.place_id,
  }));
};
