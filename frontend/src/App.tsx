import { Navigate, Route, Routes } from "react-router-dom";

import { ParticipantLayout } from "./layouts/ParticipantLayout";
import { OrganizerLayout } from "./layouts/OrganizerLayout";

import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { CadastroPage } from "./pages/auth/CadastroPage";

import { HomePage } from "./pages/participante/HomePage";
import { SearchPage } from "./pages/participante/SearchPage";
import { EventoPage } from "./pages/participante/EventoPage";
import { CheckoutPage } from "./pages/participante/CheckoutPage";
import { TicketsPage } from "./pages/participante/TicketsPage";
import { MyTicketsPage } from "./pages/participante/MyTicketsPage";

import { DashboardPage } from "./pages/organizador/DashboardPage";
import { OrgEventoPage } from "./pages/organizador/OrgEventoPage";
import { LotesPage } from "./pages/organizador/LotesPage";
import { CheckinPage } from "./pages/organizador/CheckinPage";
import { CreateEventPage } from "./pages/organizador/CreateEventPage";
import { FinancePage } from "./pages/organizador/FinancePage";
import { AttendeesPage } from "./pages/organizador/AttendeesPage";

export const App = () => (
  <Routes>
    {/* Públicas + auth (sem layout de persona) */}
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/cadastro" element={<CadastroPage />} />

    {/* Vitrine e fluxo do participante (tema escuro) */}
    <Route element={<ParticipantLayout />}>
      <Route path="/inicio" element={<HomePage />} />
      <Route path="/eventos" element={<SearchPage />} />
      <Route path="/eventos/:id" element={<EventoPage />} />
      <Route path="/eventos/:id/checkout" element={<CheckoutPage />} />
      <Route path="/eventos/:id/ingressos" element={<TicketsPage />} />
      <Route path="/meus-ingressos" element={<MyTicketsPage />} />
    </Route>

    {/* Organizador (tema claro) */}
    <Route path="/organizador" element={<OrganizerLayout />}>
      <Route index element={<DashboardPage />} />
      <Route path="evento" element={<OrgEventoPage />} />
      <Route path="eventos/novo" element={<CreateEventPage />} />
      <Route path="lotes" element={<LotesPage />} />
      <Route path="checkin" element={<CheckinPage />} />
      <Route path="participantes" element={<AttendeesPage />} />
      <Route path="financeiro" element={<FinancePage />} />
    </Route>

    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);
