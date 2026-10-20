import { useMutation } from "@tanstack/react-query";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { createTrainerProfile, registerUser } from "../../api/auth";
import type { UserRole } from "../../api/types";
import { homePathFor } from "../../auth/paths";
import { useAuth } from "../../auth/useAuth";
import "./auth.css";

const SPECIALIZATIONS = [
  "Strength & Conditioning",
  "Weight Loss",
  "Functional Fitness",
  "Yoga & Mobility",
  "Sports Performance",
  "Post-natal Fitness",
  "General Personal Training",
];

type RegisterForm = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
  role: UserRole;
  specialization: string;
  bio: string;
};

const EMPTY_FORM: RegisterForm = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  confirm_password: "",
  role: "client",
  specialization: SPECIALIZATIONS[0],
  bio: "",
};

type FieldElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

export function RegisterPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterForm>(EMPTY_FORM);
  const [passwordMismatch, setPasswordMismatch] = useState(false);

  const registration = useMutation({
    mutationFn: async () => {
      await registerUser({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
        role: form.role,
      });
      const newUser = await login(form.email, form.password);
      if (newUser.role === "trainer") {
        await createTrainerProfile({
          specialization: form.specialization,
          bio: form.bio.trim() || null,
        });
      }
      return newUser;
    },
    onSuccess: (newUser) =>
      navigate(newUser.role === "trainer" ? "/trainer" : "/onboarding", {
        replace: true,
      }),
  });

  if (user && registration.isIdle) {
    return <Navigate to={homePathFor(user.role)} replace />;
  }

  function update(field: keyof RegisterForm) {
    return (event: ChangeEvent<FieldElement>) =>
      setForm({ ...form, [field]: event.target.value });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (form.password !== form.confirm_password) {
      setPasswordMismatch(true);
      return;
    }
    setPasswordMismatch(false);
    registration.mutate();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="logo">
          Phase<span>ly</span>
        </div>
        <h1 className="auth-title">Create account</h1>
        <div className="auth-underline" />

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="role-switch">
            {(["client", "trainer"] as const).map((role) => (
              <button
                key={role}
                type="button"
                className={form.role === role ? "active" : ""}
                onClick={() => setForm({ ...form, role })}
              >
                {role === "client" ? "I'm a client" : "I'm a trainer"}
              </button>
            ))}
          </div>

          <div className="auth-row">
            <input
              className="auth-input"
              placeholder="First name"
              autoComplete="given-name"
              value={form.first_name}
              onChange={update("first_name")}
              required
            />
            <input
              className="auth-input"
              placeholder="Last name"
              autoComplete="family-name"
              value={form.last_name}
              onChange={update("last_name")}
              required
            />
          </div>
          <input
            className="auth-input"
            type="email"
            placeholder="Email"
            autoComplete="email"
            value={form.email}
            onChange={update("email")}
            required
          />

          {form.role === "trainer" && (
            <>
              <select
                className="auth-input"
                value={form.specialization}
                onChange={update("specialization")}
              >
                {SPECIALIZATIONS.map((specialization) => (
                  <option key={specialization} value={specialization}>
                    {specialization}
                  </option>
                ))}
              </select>
              <textarea
                className="auth-input"
                placeholder="Short bio (optional)"
                rows={3}
                value={form.bio}
                onChange={update("bio")}
              />
            </>
          )}

          <input
            className="auth-input"
            type="password"
            placeholder="Password (at least 8 characters)"
            autoComplete="new-password"
            minLength={8}
            value={form.password}
            onChange={update("password")}
            required
          />
          <input
            className="auth-input"
            type="password"
            placeholder="Confirm password"
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={update("confirm_password")}
            required
          />

          {passwordMismatch && (
            <p className="form-error auth-error">Passwords don't match.</p>
          )}
          {registration.error && (
            <p className="form-error auth-error">
              {registration.error.message}
            </p>
          )}
          <button
            className="btn-auth"
            type="submit"
            disabled={registration.isPending}
          >
            {registration.isPending ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-toggle">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
