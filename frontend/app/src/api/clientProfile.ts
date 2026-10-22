import { api, ApiError } from "./client";
import type { ClientProfile, IsoDate, TrainerProfile } from "./types";

export const CLIENT_PROFILE_QUERY_KEY = ["client-profile"];

export async function getMyClientProfile(): Promise<ClientProfile | null> {
  try {
    return await api.get<ClientProfile>("/client/");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function browseTrainers(): Promise<TrainerProfile[]> {
  return api.get<TrainerProfile[]>("/trainer/browse_trainers");
}

export type ClientProfileData = {
  trainer_id: string;
  fitness_goal: string | null;
  cycle_length_days: number;
  period_length_days: number;
  last_period_start: IsoDate | null;
};

export function createClientProfile(
  data: ClientProfileData,
): Promise<ClientProfile> {
  return api.post<ClientProfile>("/client/create", data);
}
