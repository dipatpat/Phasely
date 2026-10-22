import { api } from "./client";
import type {
  ExerciseLog,
  IsoDate,
  IsoDateTime,
  MealLog,
  MealType,
} from "./types";

export function mealLogsQueryKey(date: IsoDate) {
  return ["meal-logs", date];
}

export function exerciseLogsQueryKey(date: IsoDate) {
  return ["exercise-logs", date];
}

function oneDay(date: IsoDate): string {
  return new URLSearchParams({ start_date: date }).toString();
}

export function listMealLogs(date: IsoDate): Promise<MealLog[]> {
  return api.get<MealLog[]>(`/log/meal?${oneDay(date)}`);
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

export function listExerciseLogs(date: IsoDate): Promise<ExerciseLog[]> {
  return api.get<ExerciseLog[]>(`/log/exercise?${oneDay(date)}`);
}

export type ExerciseLogData = {
  exercise_id: string;
  completed_at: IsoDateTime;
  notes: string | null;
};

export function createExerciseLog(data: ExerciseLogData): Promise<ExerciseLog> {
  return api.post<ExerciseLog>("/log/exercise/create", data);
}
