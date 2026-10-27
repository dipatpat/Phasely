import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";
import { EXERCISES_QUERY_KEY, listExercises } from "../../api/library";
import {
  addTrainingAssignment,
  clientPlanQueryKey,
  createTrainingPlan,
  getClientTrainingPlan,
  removeTrainingAssignment,
  archiveTrainingPlan,
} from "../../api/plans";
import { CLIENT_OVERVIEW_QUERY_KEY, getClient } from "../../api/trainer";
import type {
  CyclePhase,
  DifficultyLevel,
  TrainingPlan,
  TrainingPlanExercise,
} from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { countByPhase, PHASE_INFO } from "../../content/phases";
import { formatPrescription, fullName } from "../../utils/format";
import { PhaseTabs } from "./PhaseTabs";
import "../client/logging.css";
import "../client/today.css";
import "./library.css";
import "./plans.css";
import "./trainer.css";

const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const DIFFICULTIES: DifficultyLevel[] = ["easy", "medium", "hard"];

function optionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

export function TrainingPlanPage() {
  const { clientId = "" } = useParams();
  const queryClient = useQueryClient();
  const planKey = clientPlanQueryKey("training", clientId);

  const client = useQuery({
    queryKey: ["client", clientId],
    queryFn: () => getClient(clientId),
  });
  const plan = useQuery({
    queryKey: planKey,
    queryFn: () => getClientTrainingPlan(clientId),
  });
  const exercises = useQuery({
    queryKey: EXERCISES_QUERY_KEY,
    queryFn: listExercises,
  });

  const [phase, setPhase] = useState<CyclePhase>("menstrual");
  const [title, setTitle] = useState("Cycle-synced training");
  const [exerciseId, setExerciseId] = useState("");
  const [day, setDay] = useState("1");
  const [difficulty, setDifficulty] = useState<DifficultyLevel>("medium");
  const [sets, setSets] = useState("");
  const [reps, setReps] = useState("");
  const [minutes, setMinutes] = useState("");
  const [weight, setWeight] = useState("");
  const [rest, setRest] = useState("");

  function showPlan(updated: TrainingPlan) {
    queryClient.setQueryData(planKey, updated);
  }

  const create = useMutation({
    mutationFn: () => createTrainingPlan(clientId, title.trim()),
    onSuccess: (created) => {
      showPlan(created);
      queryClient.invalidateQueries({ queryKey: CLIENT_OVERVIEW_QUERY_KEY });
    },
  });
  const add = useMutation({
    mutationFn: (planId: string) =>
      addTrainingAssignment(planId, {
        exercise_id: exerciseId,
        cycle_phase: phase,
        day_of_week: Number(day),
        sets: optionalNumber(sets),
        reps: optionalNumber(reps),
        duration_seconds:
          minutes.trim() === "" ? null : Math.round(Number(minutes) * 60),
        weight_kg: optionalNumber(weight),
        rest_seconds: optionalNumber(rest),
        difficulty_level: difficulty,
      }),
    onSuccess: (updated) => {
      showPlan(updated);
      setExerciseId("");
    },
  });
  const remove = useMutation({
    mutationFn: ({
      planId,
      item,
    }: {
      planId: string;
      item: TrainingPlanExercise;
    }) =>
      removeTrainingAssignment(planId, {
        exercise_id: item.exercise.id,
        cycle_phase: item.cycle_phase,
        day_of_week: item.day_of_week,
      }),
    onSuccess: showPlan,
  });

  const archive = useMutation({
    mutationFn: (planId: string) => archiveTrainingPlan(planId),
    onSuccess: () => {
      queryClient.setQueryData(planKey, null);
      queryClient.invalidateQueries({ queryKey: CLIENT_OVERVIEW_QUERY_KEY });
    },
  });

  if (client.isPending || plan.isPending || exercises.isPending) {
    return <LoadingScreen />;
  }
  if (client.isError || plan.isError || exercises.isError) {
    return <p className="form-error">Could not load the training plan.</p>;
  }

  const current = plan.data;
  const name = fullName(client.data);
  const header = (
    <>
      <Link className="back-link" to={`/trainer/clients/${clientId}`}>
        ← Back to {name}
      </Link>
      <div className="top-bar">
        <h1>Training plan</h1>
        {current && (
          <button
            type="button"
            className="btn-danger btn-small"
            disabled={archive.isPending}
            onClick={() => {
              if (
                window.confirm(
                  `Archive "${current.title}"? ${name} will have no training plan until you create a new one. The old plan is kept as history.`,
                )
              ) {
                archive.mutate(current.id);
              }
            }}
          >
            Archive plan
          </button>
        )}
      </div>
      {archive.error && <p className="form-error">{archive.error.message}</p>}

      <p className="date-tag">
        {name}
        {current && ` · ${current.title}`}
      </p>
    </>
  );

  if (current === null) {
    return (
      <>
        {header}
        <form
          className="card create-plan"
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
        >
          <p className="empty-text">{name} has no active training plan yet.</p>
          <div className="form-group">
            <label htmlFor="plan-title">Plan title</label>
            <input
              id="plan-title"
              className="form-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
            />
          </div>
          {create.error && <p className="form-error">{create.error.message}</p>}
          <button
            type="submit"
            className="btn-primary"
            disabled={create.isPending}
          >
            Create plan
          </button>
        </form>
      </>
    );
  }

  const sortedExercises = [...exercises.data].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  const inPhase = current.exercises.filter(
    (item) => item.cycle_phase === phase,
  );
  const numberFields = [
    { id: "sets", label: "Sets", value: sets, set: setSets, step: 1 },
    { id: "reps", label: "Reps", value: reps, set: setReps, step: 1 },
    {
      id: "minutes",
      label: "Duration (min)",
      value: minutes,
      set: setMinutes,
      step: 0.5,
    },
    {
      id: "weight",
      label: "Weight (kg)",
      value: weight,
      set: setWeight,
      step: 0.5,
    },
    { id: "rest", label: "Rest (s)", value: rest, set: setRest, step: 5 },
  ];

  return (
    <>
      {header}
      <PhaseTabs
        selected={phase}
        counts={countByPhase(current.exercises)}
        onSelect={setPhase}
      />

      <form
        className="card add-card"
        onSubmit={(event) => {
          event.preventDefault();
          add.mutate(current.id);
        }}
      >
        <div className="card-title">
          Add an exercise to the {PHASE_INFO[phase].label.toLowerCase()} phase
        </div>
        <div className="training-fields">
          <div>
            <label htmlFor="exercise">Exercise</label>
            <select
              id="exercise"
              className="form-input"
              value={exerciseId}
              onChange={(event) => setExerciseId(event.target.value)}
              required
            >
              <option value="">Choose…</option>
              {sortedExercises.map((exercise) => (
                <option key={exercise.id} value={exercise.id}>
                  {exercise.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="day">Day</label>
            <select
              id="day"
              className="form-input"
              value={day}
              onChange={(event) => setDay(event.target.value)}
            >
              {DAY_NAMES.map((dayName, index) => (
                <option key={dayName} value={index + 1}>
                  {dayName}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="difficulty">Difficulty</label>
            <select
              id="difficulty"
              className="form-input capitalize"
              value={difficulty}
              onChange={(event) =>
                setDifficulty(event.target.value as DifficultyLevel)
              }
            >
              {DIFFICULTIES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          {numberFields.map((field) => (
            <div key={field.id}>
              <label htmlFor={field.id}>{field.label}</label>
              <input
                id={field.id}
                className="form-input"
                type="number"
                min={field.id === "weight" || field.id === "rest" ? 0 : 1}
                step={field.step}
                placeholder="—"
                value={field.value}
                onChange={(event) => field.set(event.target.value)}
              />
            </div>
          ))}
        </div>
        <button type="submit" className="btn-primary" disabled={add.isPending}>
          Add to {DAY_NAMES[Number(day) - 1]}
        </button>
        {add.error && <p className="form-error">{add.error.message}</p>}
      </form>

      {remove.error && <p className="form-error">{remove.error.message}</p>}
      <div className="day-grid">
        {DAY_NAMES.map((dayName, index) => {
          const items = inPhase.filter(
            (item) => item.day_of_week === index + 1,
          );
          return (
            <div key={dayName} className="card">
              <div className="card-title">{dayName}</div>
              {items.length === 0 && <p className="empty-text">Rest day.</p>}
              {items.map((item) => (
                <div key={item.exercise.id} className="log-row">
                  <div>
                    <div className="exercise-name">{item.exercise.name}</div>
                    <div className="exercise-params">
                      {formatPrescription(item) || "No prescription"}
                    </div>
                  </div>
                  <div className="log-row-actions">
                    {item.difficulty_level && (
                      <span
                        className={`difficulty-chip diff-${item.difficulty_level}`}
                      >
                        {item.difficulty_level}
                      </span>
                    )}
                    <button
                      type="button"
                      className="btn-danger btn-small"
                      aria-label={`Remove ${item.exercise.name}`}
                      disabled={remove.isPending}
                      onClick={() =>
                        remove.mutate({ planId: current.id, item })
                      }
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      <p className="hint">
        To change an exercise's prescription, remove it and add it again.
        Difficulty decides when it's shown: on low-energy days clients only see
        easy exercises.
      </p>
    </>
  );
}
