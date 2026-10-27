import { api, orNull } from "./client";
import type {
  CyclePhase,
  DifficultyLevel,
  MealType,
  NutritionPlan,
  TrainingPlan,
} from "./types";

export function clientPlanQueryKey(
  kind: "nutrition" | "training",
  clientId: string,
) {
  return ["plan", kind, clientId];
}

export function getClientNutritionPlan(
  clientId: string,
): Promise<NutritionPlan | null> {
  return orNull(api.get<NutritionPlan>(`/plan/nutrition/client/${clientId}`));
}

export function getClientTrainingPlan(
  clientId: string,
): Promise<TrainingPlan | null> {
  return orNull(api.get<TrainingPlan>(`/plan/training/client/${clientId}`));
}

export type NutritionAssignment = {
  recipe_id: string;
  meal_type: MealType;
  cycle_phase: CyclePhase;
};

export type TrainingAssignment = {
  exercise_id: string;
  cycle_phase: CyclePhase;
  day_of_week: number;
  sets?: number | null;
  reps?: number | null;
  duration_seconds?: number | null;
  weight_kg?: number | null;
  rest_seconds?: number | null;
  difficulty_level?: DifficultyLevel | null;
};

export function createNutritionPlan(
  clientId: string,
  title: string,
): Promise<NutritionPlan> {
  return api.post<NutritionPlan>("/plan/nutrition/create", {
    client_id: clientId,
    title,
    recipes: [],
  });
}

// The update endpoint appends the given assignments to the plan
export function addNutritionAssignment(
  planId: string,
  assignment: NutritionAssignment,
): Promise<NutritionPlan> {
  return api.patch<NutritionPlan>(`/plan/nutrition/update?plan_id=${planId}`, {
    recipes: [assignment],
  });
}

export function removeNutritionAssignment(
  planId: string,
  assignment: NutritionAssignment,
): Promise<NutritionPlan> {
  return api.patch<NutritionPlan>(
    `/plan/nutrition/remove_recipe?plan_id=${planId}`,
    [assignment],
  );
}

export function createTrainingPlan(
  clientId: string,
  title: string,
): Promise<TrainingPlan> {
  return api.post<TrainingPlan>("/plan/training/create", {
    client_id: clientId,
    title,
    exercises: [],
  });
}

export function addTrainingAssignment(
  planId: string,
  assignment: TrainingAssignment,
): Promise<TrainingPlan> {
  return api.patch<TrainingPlan>(`/plan/training/update?plan_id=${planId}`, {
    exercises: [assignment],
  });
}

export function removeTrainingAssignment(
  planId: string,
  assignment: TrainingAssignment,
): Promise<TrainingPlan> {
  return api.patch<TrainingPlan>(
    `/plan/training/remove_exercise?plan_id=${planId}`,
    [assignment],
  );
}

export function archiveNutritionPlan(planId: string): Promise<NutritionPlan> {
  return api.patch<NutritionPlan>(`/plan/nutrition/update?plan_id=${planId}`, {
    is_active: false,
  });
}

export function archiveTrainingPlan(planId: string): Promise<TrainingPlan> {
  return api.patch<TrainingPlan>(`/plan/training/update?plan_id=${planId}`, {
    is_active: false,
  });
}
