import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";
import {
  getWeeklyReport,
  requestWeeklyReport,
  weeklyReportQueryKey,
} from "../../api/reports";
import type { DailyBreakdown } from "../../api/types";
import { PhaseBadge } from "../../components/PhaseBadge";
import { formatDayLabel, formatWeekday, weekStartIso } from "../../utils/dates";
import "../trainer/trainer.css";
import "./progress.css";

const WEEKS = [
  { label: "This week", start: weekStartIso(0) },
  { label: "Last week", start: weekStartIso(1) },
  { label: "2 weeks ago", start: weekStartIso(2) },
  { label: "3 weeks ago", start: weekStartIso(3) },
];
const POLL_FOR_MS = 8000;

export function ProgressPage() {
  const { clientId } = useParams();
  const [weekStart, setWeekStart] = useState(WEEKS[1].start);
  const [isWaiting, setIsWaiting] = useState(false);

  const report = useQuery({
    queryKey: weeklyReportQueryKey(weekStart, clientId),
    queryFn: () => getWeeklyReport(weekStart, clientId),
    refetchInterval: isWaiting ? 1500 : false,
  });

  const generate = useMutation({
    mutationFn: () => requestWeeklyReport(weekStart, clientId),
    onSuccess: () => {
      setIsWaiting(true);
      setTimeout(() => setIsWaiting(false), POLL_FOR_MS);
    },
  });

  const data = report.data;
  const showWaiting = isWaiting && !data;

  return (
    <>
      {clientId && (
        <Link className="back-link" to={`/trainer/clients/${clientId}`}>
          ← Back to client
        </Link>
      )}
      <div className="top-bar">
        <h1>Weekly progress</h1>
        {data && (
          <button
            type="button"
            className="btn-cancel btn-small"
            disabled={generate.isPending || isWaiting}
            onClick={() => generate.mutate()}
          >
            {isWaiting ? "Updating…" : "Regenerate"}
          </button>
        )}
      </div>
      <p className="date-tag">
        Reports are generated in the background (Celery) every Monday at 06:00,
        or on request.
      </p>

      <div className="filter-chips week-chips">
        {WEEKS.map((week) => (
          <button
            key={week.start}
            type="button"
            className={
              week.start === weekStart ? "filter-chip active" : "filter-chip"
            }
            onClick={() => setWeekStart(week.start)}
          >
            {week.label}
          </button>
        ))}
      </div>

      {report.isPending && <p className="loading">Loading…</p>}
      {report.isError && <p className="form-error">{report.error.message}</p>}
      {generate.error && <p className="form-error">{generate.error.message}</p>}

      {!report.isPending && !data && (
        <div className="card">
          <p className="empty-text">
            {showWaiting
              ? "Generating the report… this takes a few seconds."
              : `No report for the week of ${formatDayLabel(weekStart)} yet.`}
          </p>
          {!showWaiting && (
            <button
              type="button"
              className="btn-primary"
              style={{ marginTop: 12 }}
              disabled={generate.isPending}
              onClick={() => generate.mutate()}
            >
              Generate report
            </button>
          )}
        </div>
      )}

      {data && (
        <>
          <div className="stats">
            <Stat label="Days logged" value={`${data.summary.days_logged}/7`} />
            <Stat
              label="Avg sleep"
              value={
                data.summary.average_hours_of_sleep === null
                  ? "—"
                  : `${data.summary.average_hours_of_sleep} h`
              }
            />
            <Stat
              label="Avg energy"
              value={
                data.summary.average_energy_level === null
                  ? "—"
                  : `${data.summary.average_energy_level}/10`
              }
            />
            <Stat
              label="Calories"
              value={data.summary.total_calories.toLocaleString("en-GB")}
            />
            <Stat
              label="Exercises"
              value={String(data.summary.total_exercises_completed)}
            />
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">Calories per day</div>
            <CaloriesChart days={data.daily_breakdown} />
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Phase</th>
                  <th>Sleep</th>
                  <th>Energy</th>
                  <th>Kcal</th>
                  <th>Protein / carbs / fat</th>
                  <th>Meals</th>
                  <th>Exercises</th>
                </tr>
              </thead>
              <tbody>
                {data.daily_breakdown.map((day) => (
                  <tr key={day.date}>
                    <td>{formatDayLabel(day.date)}</td>
                    <td>
                      <PhaseBadge phase={day.cycle_phase} />
                    </td>
                    <td>
                      {day.hours_of_sleep === null
                        ? "—"
                        : `${day.hours_of_sleep} h`}
                    </td>
                    <td>
                      {day.energy_level === null
                        ? "—"
                        : `${day.energy_level}/10`}
                    </td>
                    <td>{day.calories_consumed}</td>
                    <td>
                      {day.protein} / {day.carbs} / {day.fat} g
                    </td>
                    <td>{day.meals_logged}</td>
                    <td>{day.exercises_completed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function CaloriesChart({ days }: { days: DailyBreakdown[] }) {
  const [hovered, setHovered] = useState<string | null>(null);
  const max = Math.max(...days.map((day) => day.calories_consumed), 1);

  return (
    <div
      className="bar-chart"
      role="img"
      aria-label="Calories per day. The exact values are in the table below."
    >
      {days.map((day) => (
        <div
          key={day.date}
          className="bar-column"
          onMouseEnter={() => setHovered(day.date)}
          onMouseLeave={() => setHovered(null)}
        >
          {hovered === day.date && (
            <div className="bar-tooltip">
              {formatDayLabel(day.date)}
              <br />
              <strong>{day.calories_consumed} kcal</strong>
              <br />P {day.protein} g · C {day.carbs} g · F {day.fat} g
            </div>
          )}
          <div className="bar-track">
            <div
              className="bar"
              style={{ height: `${(day.calories_consumed / max) * 100}%` }}
            />
          </div>
          <span className="bar-label">{formatWeekday(day.date)}</span>
          <PhaseBadge phase={day.cycle_phase} />
        </div>
      ))}
    </div>
  );
}
