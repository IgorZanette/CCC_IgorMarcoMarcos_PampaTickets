// Guard de rota: exige usuário logado (e, opcionalmente, um perfil específico).
// Sem usuário → redireciona para /login. Perfil errado → volta para a vitrine.

import { Navigate, Outlet, useLocation } from "react-router-dom";

import type { Perfil } from "../api/auth";
import { useCurrentUser } from "../lib/auth-store";

type Props = {
  perfil?: Perfil;
};

export const RequireAuth = ({ perfil }: Props) => {
  const user = useCurrentUser();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (perfil && user.perfil !== perfil) {
    return <Navigate to="/inicio" replace />;
  }

  return <Outlet />;
};
