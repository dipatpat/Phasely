import { api } from "./client";
import type { ClientOverview, ClientProfile } from "./types";

export const CLIENT_OVERVIEW_QUERY_KEY = ["client-overview"];

export function getClientOverview(): Promise<ClientOverview[]> {
  return api.get<ClientOverview[]>("/trainer/my_clients/overview");
}

export function getClient(clientId: string): Promise<ClientProfile> {
  return api.get<ClientProfile>(`/client/${clientId}`);
}
