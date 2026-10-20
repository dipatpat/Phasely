import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { User } from "../api/types";
import { getToken } from "../auth/tokenStorage";

export function DevHomePage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<{ status: string }>("/health"),
  });

  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/auth/me"),
    enabled: getToken() !== null,
  });

  const apiStatus = health.isPending
    ? "checking"
    : health.isSuccess
      ? "ok"
      : "unreachable";

  let session = "Not logged in";
  if (me.data) {
    session = `Logged in as ${me.data.first_name} ${me.data.last_name} (${me.data.role})`;
  } else if (me.error) {
    session = `Token rejected: ${me.error.message}`;
  }

  return (
    <main className="main">
      <div className="top-bar">
        <h1>
          Phase<span style={{ color: "var(--color-accent)" }}>ly</span>
        </h1>
      </div>
      <p className="date-tag">API status: {apiStatus}</p>
      <p className="date-tag">{session}</p>
      <div className="grid-2">
        <Link className="card card-link" to="/client">
          Open client layout →
        </Link>
        <Link className="card card-link" to="/trainer">
          Open trainer layout →
        </Link>
      </div>
    </main>
  );
}
