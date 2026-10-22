import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { createDailyLog, todayLogQueryKey } from "../../api/dailyLog";
import type { CyclePhase } from "../../api/types";
import { Modal } from "../../components/Modal";
import { ENERGY_OPTIONS } from "../../content/energy";
import { PHASE_INFO, PHASES } from "../../content/phases";
import { todayIso } from "../../utils/dates";

type DailyLogModalProps = {
  onClose: () => void;
};

export function DailyLogModal({ onClose }: DailyLogModalProps) {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<CyclePhase | "auto">("auto");
  const [periodStarted, setPeriodStarted] = useState(false);
  const [sleep, setSleep] = useState("7.5");
  const [energy, setEnergy] = useState<number | null>(null);

  const saveLog = useMutation({
    mutationFn: () =>
      createDailyLog({
        log_date: todayIso(),
        period_started_today: periodStarted,
        cycle_phase: phase === "auto" ? null : phase,
        hours_of_sleep: Number(sleep),
        energy_level: energy,
      }),
    onSuccess: (saved) => {
      queryClient.setQueryData(
        todayLogQueryKey(saved.daily_log.log_date),
        saved,
      );
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveLog.mutate();
  }

  return (
    <Modal title="Today's log" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <span className="field-label">Cycle phase</span>
          <div className="phase-selector">
            <button
              type="button"
              className={
                phase === "auto"
                  ? "phase-option auto selected"
                  : "phase-option auto"
              }
              onClick={() => setPhase("auto")}
            >
              ✨ Calculate from my cycle
            </button>
            {PHASES.map((option) => (
              <button
                key={option}
                type="button"
                className={`phase-option ${option}${phase === option ? " selected" : ""}`}
                onClick={() => setPhase(option)}
              >
                <span className={`phase-dot dot-${option}`} />
                {PHASE_INFO[option].label}
              </button>
            ))}
          </div>
          <p className="hint">
            Phasely calculates your phase from your period history. Choose one
            yourself if it doesn't feel right.
          </p>
        </div>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={periodStarted}
            onChange={(event) => setPeriodStarted(event.target.checked)}
          />
          My period started today
        </label>

        <div className="form-group">
          <label htmlFor="sleep">Hours of sleep: {Number(sleep)} h</label>
          <input
            id="sleep"
            className="sleep-slider"
            type="range"
            min={0}
            max={12}
            step={0.5}
            value={sleep}
            onChange={(event) => setSleep(event.target.value)}
          />
        </div>

        <div className="form-group">
          <span className="field-label">Energy level</span>
          <div className="energy-selector">
            {ENERGY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={
                  energy === option.value ? "energy-btn selected" : "energy-btn"
                }
                onClick={() => setEnergy(option.value)}
              >
                {option.emoji}
                <div className="energy-label">{option.label}</div>
              </button>
            ))}
          </div>
        </div>

        {saveLog.error && <p className="form-error">{saveLog.error.message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-save"
            disabled={energy === null || saveLog.isPending}
          >
            {saveLog.isPending ? "Saving…" : "Save log"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
