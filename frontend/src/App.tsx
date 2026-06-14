import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { me } from "./api/auth";
import { getToken } from "./api/client";
import { RequireAuth } from "./components/RequireAuth";
import { ParticipantLayout } from "./layouts/ParticipantLayout";
import { OrganizerLayout } from "./layouts/OrganizerLayout";

import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { CadastroPage } from "./pages/auth/CadastroPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { ValidateCodePage } from "./pages/auth/ValidateCodePage";
import { ResetPasswordPage } from "./pages/auth/ResetPasswordPage";
import { ConfirmarEmailPage } from "./pages/auth/ConfirmarEmailPage";

import { HomePage } from "./pages/participante/HomePage";
import { SearchPage } from "./pages/participante/SearchPage";
import { EventoPage } from "./pages/participante/EventoPage";
import { CheckoutPage } from "./pages/participante/CheckoutPage";
import { PagamentoStatusPage } from "./pages/participante/PagamentoStatusPage";
import { TicketsPage } from "./pages/participante/TicketsPage";
import { MyTicketsPage } from "./pages/participante/MyTicketsPage";

import { DashboardPage } from "./pages/organizador/DashboardPage";
import { OrgEventoPage } from "./pages/organizador/OrgEventoPage";
import { LotesPage } from "./pages/organizador/LotesPage";
import { CheckinPage } from "./pages/organizador/CheckinPage";
import { CreateEventPage } from "./pages/organizador/CreateEventPage";
import { FinancePage } from "./pages/organizador/FinancePage";
import { AttendeesPage } from "./pages/organizador/AttendeesPage";
import { CuponsPage } from "./pages/organizador/CuponsPage";
import { CortesiasPage } from "./pages/organizador/CortesiasPage";

export const App = () => {
  // #18: revalida a sessão no carregamento — reidrata o usuário guardado e, se o
  // token estiver inválido/expirado, o interceptor de 401 limpa a sessão.
  useEffect(() => {
    if (getToken()) {
      me().catch(() => undefined);
    }
  }, []);

  return (
    <>
      <Toaster
        position="bottom-right"
        richColors
        closeButton
        toastOptions={{ style: { fontFamily: "var(--pt-font-sans)" } }}
      />
      <Routes>
      {/* Públicas + auth (sem layout de persona) */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/cadastro" element={<CadastroPage />} />
      <Route path="/esqueci-senha" element={<ForgotPasswordPage />} />
      <Route path="/validar-codigo" element={<ValidateCodePage />} />
      <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
      <Route path="/confirmar-email" element={<ConfirmarEmailPage />} />

      {/* Vitrine e fluxo do participante (tema escuro) */}
      <Route element={<ParticipantLayout />}>
        {/* Navegação pública (vitrine) */}
        <Route path="/inicio" element={<HomePage />} />
        <Route path="/eventos" element={<SearchPage />} />
        <Route path="/eventos/:id" element={<EventoPage />} />

        {/* Fluxo que exige login */}
        <Route element={<RequireAuth />}>
          <Route path="/eventos/:id/checkout" element={<CheckoutPage />} />
          <Route
            path="/eventos/:id/pagamento/:pedidoId"
            element={<PagamentoStatusPage />}
          />
          <Route path="/eventos/:id/ingressos" element={<TicketsPage />} />
          <Route path="/meus-ingressos" element={<MyTicketsPage />} />
        </Route>
      </Route>

      {/* Organizador (tema claro) — exige login com perfil ORGANIZADOR */}
      <Route element={<RequireAuth perfil="ORGANIZADOR" />}>
        <Route path="/organizador" element={<OrganizerLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="eventos/novo" element={<CreateEventPage />} />
          <Route path="eventos/:id" element={<OrgEventoPage />} />
          <Route path="eventos/:id/lotes" element={<LotesPage />} />
          <Route path="eventos/:id/cupons" element={<CuponsPage />} />
          <Route path="eventos/:id/cortesias" element={<CortesiasPage />} />
          <Route path="eventos/:id/checkin" element={<CheckinPage />} />
          <Route path="eventos/:id/participantes" element={<AttendeesPage />} />
          <Route path="eventos/:id/financeiro" element={<FinancePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};
