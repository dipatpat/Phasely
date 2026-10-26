import type { CyclePhase } from "../api/types";

export type PhaseInfo = {
  label: string;
  icon: string;
  summary: string;
  traits: string[];
};

export const PHASE_INFO: Record<CyclePhase, PhaseInfo> = {
  menstrual: {
    label: "Menstrual",
    icon: "🌙",
    summary: "Rest and recovery",
    traits: ["Lower energy", "Gentle movement", "Iron-rich foods"],
  },
  follicular: {
    label: "Follicular",
    icon: "🌱",
    summary: "Rising energy",
    traits: ["↑ Energy", "↑ Strength", "Good for strength training"],
  },
  ovulatory: {
    label: "Ovulatory",
    icon: "☀️",
    summary: "Peak energy",
    traits: ["Peak strength", "Good for HIIT", "Protein-rich foods"],
  },
  luteal: {
    label: "Luteal",
    icon: "🍂",
    summary: "Winding down",
    traits: ["Moderate intensity", "Complex carbs", "Magnesium-rich foods"],
  },
};

export const PHASES: CyclePhase[] = [
  "menstrual",
  "follicular",
  "ovulatory",
  "luteal",
];

export function countByPhase(
  items: { cycle_phase: CyclePhase }[],
): Record<CyclePhase, number> {
  const counts: Record<CyclePhase, number> = {
    menstrual: 0,
    follicular: 0,
    ovulatory: 0,
    luteal: 0,
  };
  for (const item of items) {
    counts[item.cycle_phase] += 1;
  }
  return counts;
}
