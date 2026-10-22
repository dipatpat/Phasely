import type { CyclePhase } from "../api/types";
import { PHASE_INFO } from "../content/phases";

export function PhaseBadge({ phase }: { phase: CyclePhase | null }) {
  if (phase === null) {
    return <span className="phase-badge phase-none">Not logged</span>;
  }
  return (
    <span className={`phase-badge phase-${phase}`}>
      {PHASE_INFO[phase].label}
    </span>
  );
}
