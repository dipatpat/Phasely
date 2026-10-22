import { api, ApiError } from "./client";
import type { CyclePhase, DailyLogWithRecommendations, IsoDate } from "./types";

export function todayLogQueryKey(date: IsoDate) {
  return ["daily-log", date];
}

export async function getTodayLog(): Promise<DailyLogWithRecommendations | null> {
  try {
    return await api.get<DailyLogWithRecommendations>("/log/daily/today");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export type DailyLogData = {
  log_date: IsoDate;
  period_started_today: boolean;
  cycle_phase: CyclePhase | null;
  hours_of_sleep: number | null;
  energy_level: number | null;
};

export function createDailyLog(
  data: DailyLogData,
): Promise<DailyLogWithRecommendations> {
  return api.post<DailyLogWithRecommendations>("/log/daily/create", data);
}
