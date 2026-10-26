import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import {
  createExercise,
  EXERCISES_QUERY_KEY,
  updateExercise,
} from "../../api/library";
import type { Exercise } from "../../api/types";
import { Modal } from "../../components/Modal";

type ExerciseFormModalProps = {
  exercise: Exercise | null;
  onClose: () => void;
};

export function ExerciseFormModal({
  exercise,
  onClose,
}: ExerciseFormModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(exercise?.name ?? "");
  const [description, setDescription] = useState(exercise?.description ?? "");

  const save = useMutation({
    mutationFn: () => {
      const data = {
        name: name.trim(),
        description: description.trim() || null,
      };
      return exercise
        ? updateExercise(exercise.id, data)
        : createExercise(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EXERCISES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["plan"] });
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <Modal
      title={exercise ? "Edit exercise" : "New exercise"}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="exercise-name">Name</label>
          <input
            id="exercise-name"
            className="form-input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="exercise-description">
            Description and instructions
          </label>
          <textarea
            id="exercise-description"
            className="form-input"
            rows={7}
            placeholder={"Short summary\n1. First step\n2. Second step"}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <p className="hint">
            One step per line — clients see the line breaks.
          </p>
        </div>
        {save.error && <p className="form-error">{save.error.message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn-save" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save exercise"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
