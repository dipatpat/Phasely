import { api, orNull } from "./client";
import type { NutritionPlan, TrainingPlan } from "./types";

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
