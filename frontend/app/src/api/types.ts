export type DecimalString = string;
export type IsoDate = string;
export type IsoDateTime = string;

export type UserRole = "trainer" | "client";
export type CyclePhase = "menstrual" | "follicular" | "ovulatory" | "luteal";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type DifficultyLevel = "easy" | "medium" | "hard";

export type Token = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
};

export type TrainerProfile = {
  id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  bio: string | null;
  specialization: string | null;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type ClientProfile = {
  id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  body_fat_percentage: DecimalString | null;
  fitness_goal: string | null;
  onboarded_at: IsoDateTime | null;
  cycle_length_days: number;
  period_length_days: number;
  last_period_start: IsoDate | null;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type Ingredient = {
  id: string;
  name: string;
  quantity: DecimalString;
  unit: string;
};

export type DietaryTag = {
  id: string;
  name: string;
};

export type Recipe = {
  id: string;
  name: string;
  meal_type: MealType;
  protein: DecimalString;
  carbs: DecimalString;
  fat: DecimalString;
  calories: number;
  serving_size: string;
  preparation_notes: string | null;
  ingredients: Ingredient[];
  dietary_tags: DietaryTag[];
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type Exercise = {
  id: string;
  name: string;
  description: string | null;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type TrainingPlanExercise = {
  exercise: Exercise;
  cycle_phase: CyclePhase;
  day_of_week: number;
  sets: number | null;
  reps: number | null;
  duration_seconds: number | null;
  weight_kg: DecimalString | null;
  rest_seconds: number | null;
  difficulty_level: DifficultyLevel | null;
};

export type DailyLog = {
  id: string;
  client_id: string;
  log_date: IsoDate;
  cycle_phase: CyclePhase;
  hours_of_sleep: DecimalString | null;
  energy_level: number | null;
  created_at: IsoDateTime;
};

export type DailyLogWithRecommendations = {
  daily_log: DailyLog;
  recommended_recipes: Recipe[];
  recommended_exercises: TrainingPlanExercise[];
};
