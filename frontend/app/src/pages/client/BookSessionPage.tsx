import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  availableSlotsQueryKey,
  bookSession,
  listAvailableSlots,
  listMySessions,
  MY_SESSIONS_QUERY_KEY,
} from "../../api/sessions";
import type { AvailabilitySlot, Session } from "../../api/types";
import { CancelSessionModal } from "../../components/CancelSessionModal";
import { LoadingScreen } from "../../components/LoadingScreen";
import { daysFromNowIso, formatDayLabel, shortTime } from "../../utils/dates";
import { SessionRow } from "../trainer/SessionRow";
import "../trainer/sessions.css";
import "../trainer/trainer.css";

const BOOKING_DAYS = Array.from({ length: 14 }, (_, index) =>
  daysFromNowIso(index),
);

export function BookSessionPage() {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(BOOKING_DAYS[0]);
  const [selected, setSelected] = useState<AvailabilitySlot | null>(null);
  const [notes, setNotes] = useState("");
  const [cancelling, setCancelling] = useState<Session | null>(null);

  const slots = useQuery({
    queryKey: availableSlotsQueryKey(date),
    queryFn: () => listAvailableSlots(date),
  });
  const sessions = useQuery({
    queryKey: MY_SESSIONS_QUERY_KEY,
    queryFn: listMySessions,
  });

  const book = useMutation({
    mutationFn: () => {
      if (selected === null) {
        throw new Error("Choose a time first.");
      }
      return bookSession(
        `${selected.slot_date}T${selected.slot_start}`,
        notes.trim() || null,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_SESSIONS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["available-slots"] });
      setSelected(null);
      setNotes("");
    },
  });

  if (sessions.isPending) {
    return <LoadingScreen />;
  }
  if (sessions.isError) {
    return <p className="form-error">Could not load your sessions.</p>;
  }

  const now = new Date();
  const bookable = (slots.data ?? []).filter(
    (slot) => new Date(`${slot.slot_date}T${slot.slot_start}`) > now,
  );
  const mine = sessions.data.filter(
    (session) =>
      (session.status === "pending" || session.status === "confirmed") &&
      new Date(session.scheduled_at) > now,
  );

  return (
    <>
      <div className="top-bar">
        <h1>Book a session</h1>
      </div>
      <p className="date-tag">With your trainer · times in Europe/Warsaw</p>

      <div className="card booking-card">
        <div className="booking-step">
          <span className="field-label">1. Pick a day</span>
          <div className="day-chips">
            {BOOKING_DAYS.map((day) => (
              <button
                key={day}
                type="button"
                className={day === date ? "filter-chip active" : "filter-chip"}
                onClick={() => {
                  setDate(day);
                  setSelected(null);
                }}
              >
                {formatDayLabel(day)}
              </button>
            ))}
          </div>
        </div>

        <div className="booking-step">
          <span className="field-label">2. Pick a time</span>
          {slots.isPending && <p className="empty-text">Loading free times…</p>}
          {!slots.isPending && bookable.length === 0 && (
            <p className="empty-text">
              No free times on this day. Try another day.
            </p>
          )}
          <div className="time-chips">
            {bookable.map((slot) => (
              <button
                key={slot.id}
                type="button"
                className={
                  selected?.id === slot.id
                    ? "filter-chip active"
                    : "filter-chip"
                }
                onClick={() => setSelected(slot)}
              >
                {shortTime(slot.slot_start)}–{shortTime(slot.slot_end)}
              </button>
            ))}
          </div>
        </div>

        <div className="booking-step">
          <label className="field-label" htmlFor="booking-notes">
            3. Notes for your trainer (optional)
          </label>
          <textarea
            id="booking-notes"
            className="form-input"
            rows={2}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>

        {book.error && <p className="form-error">{book.error.message}</p>}
        <button
          type="button"
          className="btn-primary"
          disabled={selected === null || book.isPending}
          onClick={() => book.mutate()}
        >
          {selected
            ? `Book ${formatDayLabel(selected.slot_date)}, ${shortTime(selected.slot_start)}`
            : "Choose a time"}
        </button>
      </div>

      <div className="card">
        <div className="card-title">My upcoming sessions</div>
        {mine.length === 0 && (
          <p className="empty-text">No upcoming sessions.</p>
        )}
        {mine.map((session) => (
          <SessionRow key={session.id} session={session} showClient={false}>
            <button
              type="button"
              className="btn-cancel"
              onClick={() => setCancelling(session)}
            >
              Cancel
            </button>
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
