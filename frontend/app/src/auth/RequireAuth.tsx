import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import type { UserRole } from "../api/types";
import { LoadingScreen } from "../components/LoadingScreen";
import { homePathFor } from "./paths";
import { useAuth } from "./useAuth";

type RequireAuthProps = {
  role: UserRole;
  children: ReactNode;
};

export function RequireAuth({ role, children }: RequireAuthProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }
  if (user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (user.role !== role) {
    return <Navigate to={homePathFor(user.role)} replace />;
  }
  return children;
}
