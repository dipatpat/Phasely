import { api } from "./client";
import type { Session } from "./types";

export const MY_SESSIONS_QUERY_KEY = ["sessions", "mine"];

export function listMySessions(): Promise<Session[]> {
  return api.get<Session[]>("/session/my_sessions");
}
