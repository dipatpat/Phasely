import type { NavItem } from "./Sidebar";

export const CLIENT_NAV: NavItem[] = [
  { to: "/client", label: "Today", end: true },
  { to: "/client/meals", label: "Meals" },
  { to: "/client/workouts", label: "Workouts" },
  { to: "/client/progress", label: "Progress" },
  { to: "/client/shopping-list", label: "Shopping list" },
  { to: "/client/sessions", label: "Book session" },
  { to: "/client/recipes", label: "Recipes" },
];

export const TRAINER_NAV: NavItem[] = [
  { to: "/trainer", label: "Dashboard", end: true },
  { to: "/trainer/clients", label: "Clients" },
  { to: "/trainer/recipes", label: "Recipes" },
  { to: "/trainer/exercises", label: "Exercises" },
  { to: "/trainer/sessions", label: "Sessions" },
  { to: "/trainer/availability", label: "Availability" },
];
