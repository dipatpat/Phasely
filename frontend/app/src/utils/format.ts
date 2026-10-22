import type { Recipe, TrainingPlanExercise } from "../api/types";

export function formatMacros(recipe: Recipe): string {
  return `P ${Number(recipe.protein)}g · C ${Number(recipe.carbs)}g · F ${Number(recipe.fat)}g`;
}

function formatDuration(seconds: number): string {
  return seconds >= 60 ? `${Math.round(seconds / 60)} min` : `${seconds} s`;
}

export function formatPrescription(item: TrainingPlanExercise): string {
  const parts: string[] = [];
  if (item.sets) parts.push(`${item.sets} sets`);
  if (item.reps) parts.push(`${item.reps} reps`);
  if (item.duration_seconds) parts.push(formatDuration(item.duration_seconds));
  if (item.weight_kg && Number(item.weight_kg) > 0) {
    parts.push(`${Number(item.weight_kg)} kg`);
  }
  if (item.rest_seconds) parts.push(`rest ${item.rest_seconds} s`);
  return parts.join(" · ");
}
