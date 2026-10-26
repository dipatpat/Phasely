import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  deleteExercise,
  EXERCISES_QUERY_KEY,
  listExercises,
} from "../../api/library";
import type { Exercise } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { ExerciseFormModal } from "./ExerciseFormModal";
import "./library.css";
import "./trainer.css";

export function ExerciseLibraryPage() {
  const queryClient = useQueryClient();
  const exercises = useQuery({
    queryKey: EXERCISES_QUERY_KEY,
    queryFn: listExercises,
  });
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Exercise | "new" | null>(null);

  const remove = useMutation({
    mutationFn: (id: string) => deleteExercise(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: EXERCISES_QUERY_KEY }),
  });

  if (exercises.isPending) {
    return <LoadingScreen />;
  }
  if (exercises.isError) {
    return <p className="form-error">Could not load exercises.</p>;
  }

  function handleDelete(exercise: Exercise) {
    if (window.confirm(`Delete "${exercise.name}"? This cannot be undone.`)) {
      remove.mutate(exercise.id);
    }
  }

  const term = search.trim().toLowerCase();
  const visible = exercises.data
    .filter((exercise) => exercise.name.toLowerCase().includes(term))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <div className="top-bar">
        <h1>Exercise library</h1>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setEditing("new")}
        >
          + New exercise
        </button>
      </div>

      <div className="client-filters">
        <input
          className="form-input client-search"
          placeholder="🔍 Search exercises"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <p className="date-tag">
        {visible.length} of {exercises.data.length} exercises
      </p>
      {remove.error && <p className="form-error">{remove.error.message}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Exercise</th>
              <th>Instructions</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {visible.map((exercise) => (
              <tr key={exercise.id}>
                <td>
                  <strong>{exercise.name}</strong>
                </td>
                <td>
                  <p className="library-description">
                    {exercise.description ?? "—"}
                  </p>
                </td>
                <td className="table-actions">
                  <button
                    type="button"
                    className="btn-cancel btn-small"
                    onClick={() => setEditing(exercise)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn-danger btn-small"
                    onClick={() => handleDelete(exercise)}
                    disabled={remove.isPending}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing !== null && (
        <ExerciseFormModal
          exercise={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
