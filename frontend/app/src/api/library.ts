import { api } from "./client";
import type { Exercise, MealType, Recipe } from "./types";

export const RECIPES_QUERY_KEY = ["recipes"];
export const EXERCISES_QUERY_KEY = ["exercises"];

export type RecipeData = {
  name: string;
  meal_type: MealType;
  protein: number;
  carbs: number;
  fat: number;
  calories: number;
  serving_size: string;
  preparation_notes: string | null;
  ingredients: { name: string; quantity: number; unit: string }[];
  dietary_tag_names: string[];
};

export function listRecipes(): Promise<Recipe[]> {
  return api.get<Recipe[]>("/recipe/");
}

export function createRecipe(data: RecipeData): Promise<Recipe> {
  return api.post<Recipe>("/recipe/create", data);
}

export function updateRecipe(id: string, data: RecipeData): Promise<Recipe> {
  return api.patch<Recipe>(`/recipe/update?recipe_id=${id}`, data);
}

export function deleteRecipe(id: string): Promise<void> {
  return api.delete<void>(`/recipe/delete?recipe_id=${id}`);
}

export type ExerciseData = {
  name: string;
  description: string | null;
};

export function listExercises(): Promise<Exercise[]> {
  return api.get<Exercise[]>("/exercise/");
}

export function createExercise(data: ExerciseData): Promise<Exercise> {
  return api.post<Exercise>("/exercise/create", data);
}

export function updateExercise(
  id: string,
  data: ExerciseData,
): Promise<Exercise> {
  return api.patch<Exercise>(`/exercise/update?exercise_id=${id}`, data);
}

export function deleteExercise(id: string): Promise<void> {
  return api.delete<void>(`/exercise/remove?exercise_id=${id}`);
}
