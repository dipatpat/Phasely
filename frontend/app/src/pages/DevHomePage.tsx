import { useEffect, useState } from "react";
import { Link } from "react-router";

const API_URL = import.meta.env.VITE_API_URL;

type ApiStatus = "checking" | "ok" | "unreachable";

export function DevHomePage() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => setStatus(response.ok ? "ok" : "unreachable"))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <main className="main">
      <div className="top-bar">
        <h1>
          Phase<span style={{ color: "var(--color-accent)" }}>ly</span>
        </h1>
      </div>
      <p className="date-tag">API status: {status}</p>
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
