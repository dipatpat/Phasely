export const ENERGY_OPTIONS = [
  { value: 2, emoji: "😴", label: "Exhausted" },
  { value: 4, emoji: "😞", label: "Low" },
  { value: 6, emoji: "😐", label: "Okay" },
  { value: 8, emoji: "😊", label: "Good" },
  { value: 10, emoji: "🚀", label: "Excellent" },
];

export function energyOptionFor(level: number) {
  return ENERGY_OPTIONS.reduce((closest, option) =>
    Math.abs(option.value - level) < Math.abs(closest.value - level)
      ? option
      : closest,
  );
}
