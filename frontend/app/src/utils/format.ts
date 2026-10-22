import type { DailyLog, Recipe, TrainingPlanExercise } from "../api/types";
import { energyOptionFor } from "../content/energy";

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

export type Macros = {
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
};

export function macrosFor(recipe: Recipe, servings: number): Macros {
  return {
    calories: Math.round(recipe.calories * servings),
    protein: Math.round(Number(recipe.protein) * servings),
    carbs: Math.round(Number(recipe.carbs) * servings),
    fat: Math.round(Number(recipe.fat) * servings),
  };
}

export function sumMacros(items: Macros[]): Macros {
  return items.reduce(
    (total, item) => ({
      calories: total.calories + item.calories,
      protein: total.protein + item.protein,
      carbs: total.carbs + item.carbs,
      fat: total.fat + item.fat,
    }),
    { calories: 0, protein: 0, carbs: 0, fat: 0 },
  );
}

export function fullName(person: {
  first_name: string | null;
  last_name: string | null;
}): string {
  return `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim();
}

export function describeDay(log: DailyLog): string {
  const parts: string[] = [];
  if (log.energy_level !== null) {
    const energy = energyOptionFor(log.energy_level);
    parts.push(`${energy.emoji} ${energy.label} energy`);
  }
  if (log.hours_of_sleep !== null) {
    parts.push(`${Number(log.hours_of_sleep)} h sleep`);
  }
  return parts.join(" · ") || "No details logged";
}
