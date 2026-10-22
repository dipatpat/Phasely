import type { ReactNode } from "react";
import { Navigate } from "react-router";
import { LoadingScreen } from "../components/LoadingScreen";
import { useClientProfile } from "../hooks/useClientProfile";

export function RequireClientProfile({ children }: { children: ReactNode }) {
  const profile = useClientProfile();

  if (profile.isPending) {
    return <LoadingScreen />;
  }
  if (profile.isError) {
    return (
      <p className="loading">
        Could not load your profile: {profile.error.message}
      </p>
    );
  }
  if (profile.data === null) {
    return <Navigate to="/onboarding" replace />;
  }
  return children;
}
