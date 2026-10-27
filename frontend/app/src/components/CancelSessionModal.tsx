import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { cancelSession, MY_SESSIONS_QUERY_KEY } from "../api/sessions";
import type { Session } from "../api/types";
import { formatDateTime } from "../utils/dates";
import { Modal } from "./Modal";

type CancelSessionModalProps = {
  session: Session;
  onClose: () => void;
};

export function CancelSessionModal({
  session,
  onClose,
}: CancelSessionModalProps) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");

  const cancel = useMutation({
    mutationFn: () => cancelSession(session.id, reason.trim() || null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_SESSIONS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["available-slots"] });
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    cancel.mutate();
  }

  return (
    <Modal title="Cancel session" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <p className="macro-preview">{formatDateTime(session.scheduled_at)}</p>
        <div className="form-group">
          <label htmlFor="reason">Reason (optional)</label>
          <textarea
            id="reason"
            className="form-input"
            rows={3}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </div>
        {cancel.error && <p className="form-error">{cancel.error.message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Keep session
          </button>
          <button
            type="submit"
            className="btn-save"
            disabled={cancel.isPending}
          >
            {cancel.isPending ? "Cancelling…" : "Cancel session"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
