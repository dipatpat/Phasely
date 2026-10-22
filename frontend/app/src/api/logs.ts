import { api } from "./client";
import type {
  DailyLog,
  ExerciseLog,
  IsoDate,
  IsoDateTime,
  MealLog,
  MealType,
} from "./types";

export type LogQuery = {
  startDate: IsoDate;
  endDate?: IsoDate;
  clientId?: string;
};

function toParams(query: LogQuery): string {
  const params = new URLSearchParams({ start_date: query.startDate });
  if (query.endDate) params.set("end_date", query.endDate);
  if (query.clientId) params.set("client_id", query.clientId);
  return params.toString();
}

export function mealLogsQueryKey(date: IsoDate) {
  return ["meal-logs", date];
}

export function exerciseLogsQueryKey(date: IsoDate) {
  return ["exercise-logs", date];
}

export function queryDailyLogs(query: LogQuery): Promise<DailyLog[]> {
  return api.get<DailyLog[]>(`/log/daily?${toParams(query)}`);
}

export function queryMealLogs(query: LogQuery): Promise<MealLog[]> {
  return api.get<MealLog[]>(`/log/meal?${toParams(query)}`);
}

export function queryExerciseLogs(query: LogQuery): Promise<ExerciseLog[]> {
  return api.get<ExerciseLog[]>(`/log/exercise?${toParams(query)}`);
}

export function listMealLogs(date: IsoDate): Promise<MealLog[]> {
  return queryMealLogs({ startDate: date });
}

export function listExerciseLogs(date: IsoDate): Promise<ExerciseLog[]> {
  return queryExerciseLogs({ startDate: date });
}

export type MealLogData = {
  recipe_id: string;
  meal_type: MealType;
  consumed_at: IsoDateTime;
  portion_quantity: number;
  portion_unit: string;
};

export function createMealLog(data: MealLogData): Promise<MealLog> {
  return api.post<MealLog>("/log/meal/create", data);
}

export type ExerciseLogData = {
  exercise_id: string;
  completed_at: IsoDateTime;
  notes: string | null;
};

export function createExerciseLog(data: ExerciseLogData): Promise<ExerciseLog> {
  return api.post<ExerciseLog>("/log/exercise/create", data);
}
