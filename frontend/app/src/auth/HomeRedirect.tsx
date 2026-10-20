import { Navigate } from "react-router";
import { LoadingScreen } from "../components/LoadingScreen";
import { homePathFor } from "./paths";
import { useAuth } from "./useAuth";

export function HomeRedirect() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }
  return <Navigate to={user ? homePathFor(user.role) : "/login"} replace />;
}
