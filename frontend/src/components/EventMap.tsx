import L from "leaflet";
import { MapContainer, Marker, TileLayer } from "react-leaflet";

import "leaflet/dist/leaflet.css";

// Ícone do marcador via CDN — evita o problema clássico de bundler com os
// assets de imagem padrão do Leaflet.
const markerIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

type EventMapProps = {
  lat: number;
  lon: number;
  height?: number;
  zoom?: number;
};

// Mapa estático (somente leitura) com um marcador na localização do evento.
export const EventMap = ({ lat, lon, height = 220, zoom = 15 }: EventMapProps) => (
  <MapContainer
    center={[lat, lon]}
    zoom={zoom}
    style={{ height, width: "100%", borderRadius: "var(--pt-r-lg)" }}
    scrollWheelZoom={false}
    attributionControl={false}
  >
    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    <Marker position={[lat, lon]} icon={markerIcon} />
  </MapContainer>
);
