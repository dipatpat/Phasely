import { api } from "./client";
import type { AvailabilitySlot, IsoDate, Session } from "./types";

export const MY_SESSIONS_QUERY_KEY = ["sessions", "mine"];
export const AVAILABILITY_QUERY_KEY = ["availability"];

export function availableSlotsQueryKey(date: IsoDate) {
  return ["available-slots", date];
}

export function listMySessions(): Promise<Session[]> {
  return api.get<Session[]>("/session/my_sessions");
}

export function confirmSession(sessionId: string): Promise<Session> {
  return api.patch<Session>(`/session/confirm?session_id=${sessionId}`);
}

export function completeSession(sessionId: string): Promise<Session> {
  return api.patch<Session>(`/session/complete?session_id=${sessionId}`);
}

export function cancelSession(
  sessionId: string,
  reason: string | null,
): Promise<Session> {
  return api.patch<Session>(`/session/cancel?session_id=${sessionId}`, {
    cancellation_reason: reason,
  });
}

export function listAvailableSlots(date: IsoDate): Promise<AvailabilitySlot[]> {
  return api.get<AvailabilitySlot[]>(
    `/session/available_slots?date_target=${date}`,
  );
}

export function bookSession(
  scheduledAt: string,
  notes: string | null,
): Promise<Session> {
  return api.post<Session>("/session/book-client", {
    scheduled_at: scheduledAt,
    notes,
  });
}

export function listMySlots(): Promise<AvailabilitySlot[]> {
  return api.get<AvailabilitySlot[]>("/trainer/availability");
}

export type SlotData = {
  slot_date: IsoDate;
  slot_start: string;
  slot_end: string;
};

export function createSlot(data: SlotData): Promise<AvailabilitySlot> {
  return api.post<AvailabilitySlot>("/trainer/availability", data);
}

export function setSlotActive(
  slotId: string,
  isActive: boolean,
): Promise<AvailabilitySlot> {
  return api.patch<AvailabilitySlot>(`/trainer/availability/${slotId}`, {
    is_active: isActive,
  });
}

export function deleteSlot(slotId: string): Promise<void> {
  return api.delete<void>(`/trainer/availability/${slotId}`);
}
