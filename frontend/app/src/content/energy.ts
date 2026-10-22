// The UI offers five levels; the backend and its intensity rules use 0-10
export const ENERGY_OPTIONS = [
  { value: 2, emoji: "😴", label: "Exhausted" },
  { value: 4, emoji: "😞", label: "Low" },
  { value: 6, emoji: "😐", label: "Okay" },
  { value: 8, emoji: "😊", label: "Good" },
  { value: 10, emoji: "🚀", label: "Excellent" },
];

// Logs created elsewhere (e.g. demo data) can hold any 0-10 value,
// so show the closest of the five levels
export function energyOptionFor(level: number) {
  return ENERGY_OPTIONS.reduce((closest, option) =>
    Math.abs(option.value - level) < Math.abs(closest.value - level)
      ? option
      : closest,
  );
}

// Mirrors ENERGY_INTENSITY_RULES in app/recommendation/service.py
// (0-3: easy only, 4-7: easy and medium, 8-10: all). Keep both in sync.
export function intensityNote(level: number | null): string | null {
  if (level === null) return null;
  if (level <= 3) {
    return "Your energy is low today, so only easy exercises are shown.";
  }
  if (level <= 7) {
    return "Moderate energy today: easy and medium exercises are shown, hard ones are skipped.";
  }
  return null;
}
