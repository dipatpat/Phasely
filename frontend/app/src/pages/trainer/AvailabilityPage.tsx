import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import {
  AVAILABILITY_QUERY_KEY,
  createSlot,
  deleteSlot,
  listMySessions,
  listMySlots,
  MY_SESSIONS_QUERY_KEY,
  setSlotActive,
} from "../../api/sessions";
import type { AvailabilitySlot, Session } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import {
  formatDayLabel,
  formatTime,
  shortTime,
  toIsoDate,
  todayIso,
} from "../../utils/dates";
import { fullName } from "../../utils/format";
import "../trainer/library.css";
import "./sessions.css";
import "./trainer.css";

function slotKey(slot: AvailabilitySlot): string {
  return `${slot.slot_date}T${shortTime(slot.slot_start)}`;
}

function sessionKey(session: Session): string {
  const start = new Date(session.scheduled_at);
  return `${toIsoDate(start)}T${formatTime(start)}`;
}

export function AvailabilityPage() {
  const queryClient = useQueryClient();
  const slots = useQuery({
    queryKey: AVAILABILITY_QUERY_KEY,
    queryFn: listMySlots,
  });
  const sessions = useQuery({
    queryKey: MY_SESSIONS_QUERY_KEY,
    queryFn: listMySessions,
  });
  const [date, setDate] = useState(todayIso());
  const [start, setStart] = useState("09:00");
  const [end, setEnd] = useState("10:00");

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: AVAILABILITY_QUERY_KEY });
  const create = useMutation({
    mutationFn: () =>
      createSlot({ slot_date: date, slot_start: start, slot_end: end }),
    onSuccess: refresh,
  });
  const toggle = useMutation({
    mutationFn: (slot: AvailabilitySlot) =>
      setSlotActive(slot.id, !slot.is_active),
    onSuccess: refresh,
  });
  const remove = useMutation({ mutationFn: deleteSlot, onSuccess: refresh });

  if (slots.isPending || sessions.isPending) {
    return <LoadingScreen />;
  }
  if (slots.isError || sessions.isError) {
    return <p className="form-error">Could not load your availability.</p>;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    create.mutate();
  }

  const bookedBy = new Map(
    sessions.data
      .filter((session) => session.status !== "cancelled")
      .map((session) => [sessionKey(session), session]),
  );
  const today = todayIso();
  const upcoming = slots.data
    .filter((slot) => slot.slot_date >= today)
    .sort((a, b) => slotKey(a).localeCompare(slotKey(b)));
  const byDate = upcoming.reduce<Record<string, AvailabilitySlot[]>>(
    (groups, slot) => {
      (groups[slot.slot_date] ??= []).push(slot);
      return groups;
    },
    {},
  );
  const invalidTime = end <= start;
  const error = create.error ?? toggle.error ?? remove.error;

  return (
    <>
      <div className="top-bar">
        <h1>Availability</h1>
      </div>
      <p className="date-tag">
        Times are in Europe/Warsaw. Clients can book any active, free slot.
      </p>

      <form className="card booking-card" onSubmit={handleSubmit}>
        <div className="card-title">Add a slot</div>
        <div className="slot-form">
          <div>
            <label htmlFor="slot-date">Date</label>
            <input
              id="slot-date"
              className="form-input"
              type="date"
              min={today}
              value={date}
              onChange={(event) => setDate(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="slot-start">Start</label>
            <input
              id="slot-start"
              className="form-input"
              type="time"
              value={start}
              onChange={(event) => setStart(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="slot-end">End</label>
            <input
              id="slot-end"
              className="form-input"
              type="time"
              value={end}
              onChange={(event) => setEnd(event.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={invalidTime || create.isPending}
          >
            Add slot
          </button>
        </div>
        {invalidTime && (
          <p className="form-error">The end must be after the start.</p>
        )}
      </form>

      {error && <p className="form-error">{error.message}</p>}
      {upcoming.length === 0 && (
        <div className="card">
          <p className="empty-text">No upcoming slots. Add some above.</p>
        </div>
      )}

      <div className="availability-days">
        {Object.entries(byDate).map(([slotDate, daySlots]) => (
          <div key={slotDate} className="card availability-day">
            <div className="card-title">{formatDayLabel(slotDate)}</div>
            <div className="slot-list">
              {daySlots.map((slot) => {
                const session = bookedBy.get(slotKey(slot));
                const state = session
                  ? "booked"
                  : slot.is_active
                    ? "free"
                    : "inactive";
                return (
                  <div key={slot.id} className={`slot-chip ${state}`}>
                    <div>
                      <div className="slot-time">
                        {shortTime(slot.slot_start)}–{shortTime(slot.slot_end)}
                      </div>
                      <div className="slot-state">
                        {session
                          ? `${fullName(session.client)} · ${session.status}`
                          : slot.is_active
                            ? "Free"
                            : "Hidden from clients"}
                      </div>
                    </div>
                    {!session && (
                      <>
                        <button
                          type="button"
                          className="icon-btn"
                          title={
                            slot.is_active
                              ? "Hide from clients"
                              : "Show to clients"
                          }
                          aria-label={
                            slot.is_active ? "Deactivate slot" : "Activate slot"
                          }
                          disabled={toggle.isPending}
                          onClick={() => toggle.mutate(slot)}
                        >
                          {slot.is_active ? "⏸" : "▶"}
                        </button>
                        <button
                          type="button"
                          className="icon-btn"
                          title="Delete slot"
                          aria-label="Delete slot"
                          disabled={remove.isPending}
                          onClick={() => remove.mutate(slot.id)}
                        >
                          ✕
                        </button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
