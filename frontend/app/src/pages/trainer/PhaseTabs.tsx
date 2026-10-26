import type { CyclePhase } from "../../api/types";
import { PHASE_INFO, PHASES } from "../../content/phases";

type PhaseTabsProps = {
  selected: CyclePhase;
  counts: Record<CyclePhase, number>;
  onSelect: (phase: CyclePhase) => void;
};

export function PhaseTabs({ selected, counts, onSelect }: PhaseTabsProps) {
  return (
    <div className="phase-tabs" role="tablist">
      {PHASES.map((phase) => (
        <button
          key={phase}
          type="button"
          role="tab"
          aria-selected={phase === selected}
          className={`phase-tab phase-${phase}${phase === selected ? " selected" : ""}`}
          onClick={() => onSelect(phase)}
        >
          {PHASE_INFO[phase].icon} {PHASE_INFO[phase].label}
          <span className="tab-count">{counts[phase]}</span>
        </button>
      ))}
    </div>
  );
}
