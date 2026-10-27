import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import {
  queryDailyLogs,
  queryExerciseLogs,
  queryMealLogs,
} from "../../api/logs";
import {
  clientPlanQueryKey,
  getClientNutritionPlan,
  getClientTrainingPlan,
} from "../../api/plans";
import { MY_SESSIONS_QUERY_KEY, listMySessions } from "../../api/sessions";
import { getClient } from "../../api/trainer";
import type {
  CyclePhase,
  DailyLog,
  ExerciseLog,
  MealLog,
} from "../../api/types";
import { Avatar } from "../../components/Avatar";
import { LoadingScreen } from "../../components/LoadingScreen";
import { PhaseBadge } from "../../components/PhaseBadge";
import { PHASES } from "../../content/phases";
import {
  daysAgoIso,
  formatRelativeDay,
  formatShortDate,
  formatTime,
  toIsoDate,
  todayIso,
} from "../../utils/dates";
import { describeDay, fullName } from "../../utils/format";
import { SessionRow } from "./SessionRow";
import "./trainer.css";

export function ClientDetailPage() {
  const { clientId = "" } = useParams();
  const today = todayIso();
  const weekAgo = daysAgoIso(6);
  const range = { startDate: weekAgo, endDate: today, clientId };

  const profile = useQuery({
    queryKey: ["client", clientId],
    queryFn: () => getClient(clientId),
  });
  const nutrition = useQuery({
    queryKey: clientPlanQueryKey("nutrition", clientId),
    queryFn: () => getClientNutritionPlan(clientId),
  });
  const training = useQuery({
    queryKey: clientPlanQueryKey("training", clientId),
    queryFn: () => getClientTrainingPlan(clientId),
  });
  const sessions = useQuery({
    queryKey: MY_SESSIONS_QUERY_KEY,
    queryFn: listMySessions,
  });
  const dailyLogs = useQuery({
    queryKey: ["daily-logs", clientId, weekAgo, today],
    queryFn: () => queryDailyLogs(range),
  });
  const mealLogs = useQuery({
    queryKey: ["meal-logs", clientId, weekAgo, today],
    queryFn: () => queryMealLogs(range),
  });
  const exerciseLogs = useQuery({
    queryKey: ["exercise-logs", clientId, weekAgo, today],
    queryFn: () => queryExerciseLogs(range),
  });

  if (profile.isPending) {
    return <LoadingScreen />;
  }
  if (profile.isError) {
    return <p className="form-error">{profile.error.message}</p>;
  }

  const client = profile.data;
  const todayLog =
    dailyLogs.data?.find((log) => log.log_date === today) ?? null;
  const now = new Date();
  const upcoming = (sessions.data ?? []).filter(
    (session) =>
      session.client.id === clientId &&
      (session.status === "pending" || session.status === "confirmed") &&
      new Date(session.scheduled_at) >= now,
  );
  const timeline = buildTimeline(
    dailyLogs.data ?? [],
    mealLogs.data ?? [],
    exerciseLogs.data ?? [],
  );
  const logsLoading =
    dailyLogs.isPending || mealLogs.isPending || exerciseLogs.isPending;

  return (
    <>
      <Link className="back-link" to="/trainer/clients">
        ← Back to clients
      </Link>
      <div className="client-header">
        <Avatar firstName={client.first_name} lastName={client.last_name} />
        <div className="row-main">
          <h1>{fullName(client)}</h1>
          <p className="row-sub">{client.email}</p>
        </div>
        <PhaseBadge phase={todayLog ? todayLog.cycle_phase : null} />
        <Link
          className="btn-cancel btn-small"
          to={`/trainer/clients/${clientId}/progress`}
        >
          Weekly summary
        </Link>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Profile</div>
          <dl className="profile-list">
            <dt>Fitness goal</dt>
            <dd>{client.fitness_goal ?? "—"}</dd>
            <dt>Body fat</dt>
            <dd>
              {client.body_fat_percentage
                ? `${Number(client.body_fat_percentage)}%`
                : "—"}
            </dd>
            <dt>Cycle length</dt>
            <dd>{client.cycle_length_days} days</dd>
            <dt>Period length</dt>
            <dd>{client.period_length_days} days</dd>
            <dt>Last period start</dt>
            <dd>
              {client.last_period_start
                ? formatShortDate(client.last_period_start)
                : "—"}
            </dd>
            <dt>Onboarded</dt>
            <dd>
              {client.onboarded_at ? formatShortDate(client.onboarded_at) : "—"}
            </dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">Upcoming sessions</div>
          {sessions.isPending && <p className="empty-text">Loading…</p>}
          {!sessions.isPending && upcoming.length === 0 && (
            <p className="empty-text">No upcoming sessions with this client.</p>
          )}
          {upcoming.map((session) => (
            <SessionRow key={session.id} session={session} showClient={false} />
          ))}
        </div>
      </div>

      <div className="grid-2">
        <PlanCard
          heading="Active nutrition plan"
          unit="recipes"
          isPending={nutrition.isPending}
          title={nutrition.data?.title ?? null}
          items={nutrition.data?.recipes ?? []}
          editTo={`/trainer/clients/${clientId}/nutrition`}
        />
        <PlanCard
          heading="Active training plan"
          unit="exercises"
          isPending={training.isPending}
          title={training.data?.title ?? null}
          items={training.data?.exercises ?? []}
          editTo={`/trainer/clients/${clientId}/training`}
        />
      </div>

      <div className="card">
        <div className="card-title">Recent logs · last 7 days</div>
        {logsLoading && <p className="empty-text">Loading…</p>}
        {!logsLoading && timeline.length === 0 && (
          <p className="empty-text">Nothing logged in the last 7 days.</p>
        )}
        {timeline.map((entry) => (
          <div key={entry.key} className="status-row">
            <div className="row-main">
              <div className="row-title">{entry.label}</div>
              <div className="row-sub">{entry.detail}</div>
            </div>
            <span className="timeline-when">{entry.when}</span>
          </div>
        ))}
      </div>
    </>
  );
}

type PlanCardProps = {
  heading: string;
  unit: string;
  isPending: boolean;
  title: string | null;
  items: { cycle_phase: CyclePhase }[];
  editTo: string;
};

function PlanCard({
  heading,
  unit,
  isPending,
  title,
  items,
  editTo,
}: PlanCardProps) {
  return (
    <div className="card">
      <div className="card-title">
        {heading}
        {!isPending && (
          <Link className="card-link" to={editTo}>
            {title === null ? "Create plan →" : "Edit plan →"}
          </Link>
        )}
      </div>
      {isPending && <p className="empty-text">Loading…</p>}
      {!isPending && title === null && (
        <p className="empty-text">No active plan yet.</p>
      )}
      {title !== null && (
        <>
          <p className="plan-title">{title}</p>
          <p className="row-sub">
            {items.length} {unit} across the cycle
          </p>
          {PHASES.map((phase) => (
            <div key={phase} className="phase-count-row">
              <PhaseBadge phase={phase} />
              <span>
                {items.filter((item) => item.cycle_phase === phase).length}{" "}
                {unit}
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

type TimelineEntry = {
  key: string;
  time: number;
  label: string;
  detail: string;
  when: string;
};

function buildTimeline(
  daily: DailyLog[],
  meals: MealLog[],
  exercises: ExerciseLog[],
): TimelineEntry[] {
  const atMoment = (iso: string) => {
    const date = new Date(iso);
    return `${formatRelativeDay(toIsoDate(date))}, ${formatTime(date)}`;
  };
  const entries: TimelineEntry[] = [
    ...daily.map((log) => ({
      key: `day-${log.id}`,
      time: new Date(`${log.log_date}T00:00:00`).getTime(),
      label: `Daily log · ${log.cycle_phase} phase`,
      detail: describeDay(log),
      when: formatRelativeDay(log.log_date),
    })),
    ...meals.map((log) => ({
      key: `meal-${log.id}`,
      time: new Date(log.consumed_at).getTime(),
      label: `Meal · ${log.recipe.name}`,
      detail: `${log.meal_type} · ${Number(log.portion_quantity)} serving(s)`,
      when: atMoment(log.consumed_at),
    })),
    ...exercises.map((log) => ({
      key: `exercise-${log.id}`,
      time: new Date(log.completed_at).getTime(),
      label: `Exercise · ${log.exercise.name}`,
      detail: log.notes ?? "completed",
      when: atMoment(log.completed_at),
    })),
  ];
  return entries.sort((a, b) => b.time - a.time);
}
