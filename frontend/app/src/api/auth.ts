import { api, apiFetch } from "./client";
import type { Token, TrainerProfile, User, UserRole } from "./types";

export const ME_QUERY_KEY = ["me"];

export function requestToken(email: string, password: string): Promise<Token> {
  return apiFetch<Token>("/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username: email, password }),
  });
}

export function getCurrentUser(): Promise<User> {
  return api.get<User>("/auth/me");
}

export function logoutRequest(): Promise<void> {
  return api.post<void>("/auth/logout");
}

export type RegisterData = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: UserRole;
};

export function registerUser(data: RegisterData): Promise<User> {
  return api.post<User>("/auth/register", data);
}

export type TrainerProfileData = {
  bio: string | null;
  specialization: string | null;
};

export function createTrainerProfile(
  data: TrainerProfileData,
): Promise<TrainerProfile> {
  return api.post<TrainerProfile>("/trainer/create", data);
}
