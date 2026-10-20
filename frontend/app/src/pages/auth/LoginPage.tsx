import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation } from "react-router";
import { homePathFor } from "../../auth/paths";
import { useAuth } from "../../auth/useAuth";
import "./auth.css";

export function LoginPage() {
  const { user, login } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => login(email, password),
  });

  if (user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? homePathFor(user.role)} replace />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="logo">
          Phase<span>ly</span>
        </div>
        <h1 className="auth-title">Log in</h1>
        <div className="auth-underline" />

        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            className="auth-input"
            type="email"
            placeholder="Email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            className="auth-input"
            type="password"
            placeholder="Password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {loginMutation.error && (
            <p className="form-error auth-error">
              {loginMutation.error.message}
            </p>
          )}
          <button
            className="btn-auth"
            type="submit"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="auth-toggle">
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
