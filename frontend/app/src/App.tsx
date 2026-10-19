import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

type ApiStatus = "checking" | "ok" | "unreachable";

function App() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => setStatus(response.ok ? "ok" : "unreachable"))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: 32 }}>
      <h1>Phasely</h1>
      <p>API status: {status}</p>
    </main>
  );
}

export default App;
