import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import {
  createExerciseLog,
  exerciseLogsQueryKey,
  listExerciseLogs,
} from "../../api/logs";
import type { TrainingPlanExercise } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { Modal } from "../../components/Modal";
import { PHASE_INFO } from "../../content/phases";
import { useTodayLog } from "../../hooks/useTodayLog";
import { formatLongDate, todayIso } from "../../utils/dates";
import { formatPrescription } from "../../utils/format";
import "./logging.css";
import "./today.css";
import { intensityNote } from "../../content/energy";

export function WorkoutsPage() {
  const today = todayIso();
  const todayLog = useTodayLog();
  const exerciseLogs = useQuery({
    queryKey: exerciseLogsQueryKey(today),
    queryFn: () => listExerciseLogs(today),
  });
  const [exerciseToLog, setExerciseToLog] =
    useState<TrainingPlanExercise | null>(null);

  if (todayLog.isPending || exerciseLogs.isPending) {
    return <LoadingScreen />;
  }
  if (todayLog.isError || exerciseLogs.isError) {
    return <p className="form-error">Could not load your workout.</p>;
  }

  const log = todayLog.data;
  const note = intensityNote(log ? log.daily_log.energy_level : null);

  const logs = exerciseLogs.data;
  const planned = log ? log.recommended_exercises : [];
  const doneIds = new Set(logs.map((entry) => entry.exercise.id));
  const doneCount = planned.filter((item) =>
    doneIds.has(item.exercise.id),
  ).length;
  const percent =
    planned.length > 0 ? Math.round((doneCount / planned.length) * 100) : 0;

  return (
    <>
      <div className="top-bar">
        <h1>Workout log</h1>
      </div>
      <p className="date-tag">
        {formatLongDate(new Date())}
        {log && ` · ${PHASE_INFO[log.daily_log.cycle_phase].label} phase`}
      </p>

      {log === null && (
        <div className="card">
          <p className="empty-text">
            Log your day on the <Link to="/client">Today</Link> page first —
            your phase and energy decide today's workout.
          </p>
        </div>
      )}

      {log !== null && planned.length === 0 && (
        <div className="card">
          {note && <p className="intensity-note">💡 {note}</p>}
          <p className="empty-text">
            Nothing planned for today at your energy level — enjoy the rest day.
          </p>
        </div>
      )}

      {planned.length > 0 && (
        <>
          <div className="card progress-card">
            <p className="progress-text">
              <strong>
                {doneCount} of {planned.length}
              </strong>{" "}
              exercises done
            </p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${percent}%` }} />
            </div>
          </div>

          <div className="card">
            <div className="card-title">Today's exercises</div>
            {note && <p className="intensity-note">💡 {note}</p>}

            {planned.map((item) => {
              const entry = logs.find(
                (logged) => logged.exercise.id === item.exercise.id,
              );
              return (
                <div key={item.exercise.id} className="log-row">
                  <div>
                    <div className="exercise-name">{item.exercise.name}</div>
                    <div className="exercise-params">
                      Plan: {formatPrescription(item)}
                    </div>
                    {entry?.notes && (
                      <div className="logged-note">✓ {entry.notes}</div>
                    )}
                  </div>
                  <div className="log-row-actions">
                    {item.difficulty_level && (
                      <span
                        className={`difficulty-chip diff-${item.difficulty_level}`}
                      >
                        {item.difficulty_level}
                      </span>
                    )}
                    {entry ? (
                      <span className="done-badge">✓ Done</span>
                    ) : (
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() => setExerciseToLog(item)}
                      >
                        Log
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {exerciseToLog && (
        <LogExerciseModal
          item={exerciseToLog}
          onClose={() => setExerciseToLog(null)}
        />
      )}
    </>
  );
}

type LogExerciseModalProps = {
  item: TrainingPlanExercise;
  onClose: () => void;
};

function LogExerciseModal({ item, onClose }: LogExerciseModalProps) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");

  const saveExercise = useMutation({
    mutationFn: () =>
      createExerciseLog({
        exercise_id: item.exercise.id,
        completed_at: new Date().toISOString(),
        notes: notes.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: exerciseLogsQueryKey(todayIso()),
      });
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveExercise.mutate();
  }

  return (
    <Modal title={`Log ${item.exercise.name}`} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <p className="macro-preview">Plan: {formatPrescription(item)}</p>
        <div className="form-group">
          <label htmlFor="notes">What did you do? (optional)</label>
          <textarea
            id="notes"
            className="form-input"
            rows={3}
            placeholder="e.g. 4 × 8 at 62 kg, felt strong"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>
        {saveExercise.error && (
          <p className="form-error">{saveExercise.error.message}</p>
        )}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-save"
            disabled={saveExercise.isPending}
          >
            {saveExercise.isPending ? "Saving…" : "Mark as done"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
