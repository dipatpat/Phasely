import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  completeSession,
  confirmSession,
  listMySessions,
  MY_SESSIONS_QUERY_KEY,
} from "../../api/sessions";
import type { Session } from "../../api/types";
import { CancelSessionModal } from "../../components/CancelSessionModal";
import { LoadingScreen } from "../../components/LoadingScreen";
import { SessionRow } from "./SessionRow";
import "./sessions.css";
import "./trainer.css";

type View = "upcoming" | "past" | "cancelled";

const VIEWS: { value: View; label: string }[] = [
  { value: "upcoming", label: "Upcoming" },
  { value: "past", label: "Past" },
  { value: "cancelled", label: "Cancelled" },
];

export function SessionsPage() {
  const queryClient = useQueryClient();
  const sessions = useQuery({
    queryKey: MY_SESSIONS_QUERY_KEY,
    queryFn: listMySessions,
  });
  const [view, setView] = useState<View>("upcoming");
  const [cancelling, setCancelling] = useState<Session | null>(null);

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: MY_SESSIONS_QUERY_KEY });
  const confirm = useMutation({
    mutationFn: confirmSession,
    onSuccess: refresh,
  });
  const complete = useMutation({
    mutationFn: completeSession,
    onSuccess: refresh,
  });

  if (sessions.isPending) {
    return <LoadingScreen />;
  }
  if (sessions.isError) {
    return <p className="form-error">Could not load sessions.</p>;
  }

  const now = new Date();
  const hasStarted = (session: Session) =>
    new Date(session.scheduled_at) <= now;
  const byView: Record<View, Session[]> = {
    upcoming: sessions.data.filter(
      (s) =>
        (s.status === "pending" || s.status === "confirmed") && !hasStarted(s),
    ),
    past: sessions.data
      .filter(
        (s) =>
          s.status !== "cancelled" &&
          (s.status === "completed" || hasStarted(s)),
      )
      .reverse(),
    cancelled: sessions.data.filter((s) => s.status === "cancelled").reverse(),
  };
  const busy = confirm.isPending || complete.isPending;

  return (
    <>
      <div className="top-bar">
        <h1>Sessions</h1>
      </div>
      <p className="date-tag">
        Confirm requests, complete sessions you've held, or cancel.
      </p>

      <div className="filter-chips view-tabs">
        {VIEWS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={
              view === option.value ? "filter-chip active" : "filter-chip"
            }
            onClick={() => setView(option.value)}
          >
            {option.label} ({byView[option.value].length})
          </button>
        ))}
      </div>

      {(confirm.error || complete.error) && (
        <p className="form-error">
          {(confirm.error ?? complete.error)?.message}
        </p>
      )}

      <div className="card">
        {byView[view].length === 0 && (
          <p className="empty-text">No sessions here.</p>
        )}
        {byView[view].map((session) => (
          <SessionRow key={session.id} session={session} showClient>
            {session.status === "pending" && !hasStarted(session) && (
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => confirm.mutate(session.id)}
              >
                Confirm
              </button>
            )}
            {session.status === "confirmed" && hasStarted(session) && (
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => complete.mutate(session.id)}
              >
                Mark completed
              </button>
            )}
            {(session.status === "pending" || session.status === "confirmed") &&
              !hasStarted(session) && (
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setCancelling(session)}
                >
                  Cancel
                </button>
              )}
          </SessionRow>
        ))}
      </div>

      {cancelling && (
        <CancelSessionModal
          session={cancelling}
          onClose={() => setCancelling(null)}
        />
      )}
    </>
  );
}
