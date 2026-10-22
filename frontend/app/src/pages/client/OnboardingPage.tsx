import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { Navigate } from "react-router";
import {
  browseTrainers,
  CLIENT_PROFILE_QUERY_KEY,
  createClientProfile,
} from "../../api/clientProfile";
import { useAuth } from "../../auth/useAuth";
import { LoadingScreen } from "../../components/LoadingScreen";
import { useClientProfile } from "../../hooks/useClientProfile";
import { todayIso } from "../../utils/dates";
import "./onboarding.css";

type OnboardingForm = {
  trainer_id: string;
  fitness_goal: string;
  last_period_start: string;
  cycle_length_days: string;
  period_length_days: string;
};

const INITIAL_FORM: OnboardingForm = {
  trainer_id: "",
  fitness_goal: "",
  last_period_start: "",
  cycle_length_days: "28",
  period_length_days: "5",
};

export function OnboardingPage() {
  const queryClient = useQueryClient();
  const { logout } = useAuth();
  const profile = useClientProfile();
  const trainers = useQuery({ queryKey: ["trainers"], queryFn: browseTrainers });
  const [form, setForm] = useState<OnboardingForm>(INITIAL_FORM);

  const onboarding = useMutation({
    mutationFn: () =>
      createClientProfile({
        trainer_id: form.trainer_id,
        fitness_goal: form.fitness_goal.trim() || null,
        last_period_start: form.last_period_start || null,
        cycle_length_days: Number(form.cycle_length_days),
        period_length_days: Number(form.period_length_days),
      }),
    onSuccess: (created) =>
      queryClient.setQueryData(CLIENT_PROFILE_QUERY_KEY, created),
  });

  if (profile.isPending) {
    return <LoadingScreen />;
  }
  if (profile.data) {
    return <Navigate to="/client" replace />;
  }

  function update(field: keyof OnboardingForm) {
    return (event: ChangeEvent<HTMLInputElement>) =>
      setForm({ ...form, [field]: event.target.value });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onboarding.mutate();
  }

  return (
    <div className="onboarding-page">
      <form className="onboarding-card" onSubmit={handleSubmit}>
        <div className="logo">
          Phase<span>ly</span>
        </div>
        <h1 className="modal-title">Welcome! Let's set up your profile</h1>
        <div className="modal-underline" />

        <section className="onboarding-section">
          <h2 className="card-title">1. Choose your trainer</h2>
          {trainers.isPending && <p className="loading">Loading trainers…</p>}
          {trainers.error && (
            <p className="form-error">{trainers.error.message}</p>
          )}
          <div className="trainer-options">
            {trainers.data?.map((trainer) => (
              <button
                key={trainer.id}
                type="button"
                className={
                  form.trainer_id === trainer.id
                    ? "trainer-option selected"
                    : "trainer-option"
                }
                onClick={() => setForm({ ...form, trainer_id: trainer.id })}
              >
                <strong>
                  {trainer.first_name} {trainer.last_name}
                </strong>
                <span>{trainer.specialization ?? "Personal trainer"}</span>
                {trainer.bio && <p>{trainer.bio}</p>}
              </button>
            ))}
          </div>
        </section>

        <section className="onboarding-section">
          <h2 className="card-title">2. Your goal</h2>
          <div className="form-group">
            <label htmlFor="fitness_goal">Fitness goal (optional)</label>
            <input
              id="fitness_goal"
              className="form-input"
              placeholder="e.g. Build strength"
              value={form.fitness_goal}
              onChange={update("fitness_goal")}
            />
          </div>
        </section>

        <section className="onboarding-section">
          <h2 className="card-title">3. Your cycle</h2>
          <p className="onboarding-hint">
            Phasely adapts your meals and workouts to the phase of your cycle.
            If you leave the date empty, you can choose your phase yourself
            each time you log your day.
          </p>
          <div className="form-group">
            <label htmlFor="last_period_start">
              First day of your last period
            </label>
            <input
              id="last_period_start"
              className="form-input"
              type="date"
              max={todayIso()}
              value={form.last_period_start}
              onChange={update("last_period_start")}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cycle_length_days">Cycle length (days)</label>
              <input
                id="cycle_length_days"
                className="form-input"
                type="number"
                min={21}
                max={45}
                value={form.cycle_length_days}
                onChange={update("cycle_length_days")}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="period_length_days">Period length (days)</label>
              <input
                id="period_length_days"
                className="form-input"
                type="number"
                min={1}
                max={10}
                value={form.period_length_days}
                onChange={update("period_length_days")}
                required
              />
            </div>
          </div>
        </section>

        {onboarding.error && (
          <p className="form-error">{onboarding.error.message}</p>
        )}
        <button
          className="btn-primary onboarding-submit"
          type="submit"
          disabled={form.trainer_id === "" || onboarding.isPending}
        >
          {onboarding.isPending ? "Saving…" : "Start using Phasely"}
        </button>
        <button type="button" className="onboarding-logout" onClick={logout}>
          Log out
        </button>
      </form>
    </div>
  );
}
