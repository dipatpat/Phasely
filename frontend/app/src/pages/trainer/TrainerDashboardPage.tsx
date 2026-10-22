import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { MY_SESSIONS_QUERY_KEY, listMySessions } from "../../api/sessions";
import {
  CLIENT_OVERVIEW_QUERY_KEY,
  getClientOverview,
} from "../../api/trainer";
import { useAuth } from "../../auth/useAuth";
import { Avatar } from "../../components/Avatar";
import { LoadingScreen } from "../../components/LoadingScreen";
import { PhaseBadge } from "../../components/PhaseBadge";
import { formatLongDate, greeting } from "../../utils/dates";
import { describeDay, fullName } from "../../utils/format";
import { SessionRow } from "./SessionRow";
import "./trainer.css";

export function TrainerDashboardPage() {
  const { user } = useAuth();
  const overview = useQuery({
    queryKey: CLIENT_OVERVIEW_QUERY_KEY,
    queryFn: getClientOverview,
  });
  const sessions = useQuery({
    queryKey: MY_SESSIONS_QUERY_KEY,
    queryFn: listMySessions,
  });

  if (overview.isPending || sessions.isPending) {
    return <LoadingScreen />;
  }
  if (overview.isError || sessions.isError) {
    return <p className="form-error">Could not load the dashboard.</p>;
  }

  const clients = overview.data;
  const now = new Date();
  const upcoming = sessions.data.filter(
    (session) =>
      (session.status === "pending" || session.status === "confirmed") &&
      new Date(session.scheduled_at) >= now,
  );
  const pendingCount = upcoming.filter((s) => s.status === "pending").length;
  const loggedCount = clients.filter((item) => item.today_log !== null).length;
  const notLogged = clients.filter((item) => item.today_log === null);

  const stats = [
    { label: "Clients", value: clients.length, sub: "assigned to you" },
    {
      label: "Upcoming sessions",
      value: upcoming.length,
      sub: `${pendingCount} waiting for confirmation`,
    },
    {
      label: "Logged today",
      value: `${loggedCount}/${clients.length}`,
      sub: "clients",
    },
  ];

  return (
    <>
      <div className="top-bar">
        <h1>
          {greeting(now)}, {user?.first_name} 👋
        </h1>
      </div>
      <p className="date-tag">{formatLongDate(now)}</p>

      <div className="stats">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-sub">{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            Upcoming sessions
            <Link className="card-link" to="/trainer/sessions">
              All sessions →
            </Link>
          </div>
          {upcoming.length === 0 && (
            <p className="empty-text">No upcoming sessions.</p>
          )}
          {upcoming.slice(0, 5).map((session) => (
            <SessionRow key={session.id} session={session} showClient />
          ))}
        </div>

        <div className="card">
          <div className="card-title">
            Today's log status
            <Link className="card-link" to="/trainer/clients">
              All clients →
            </Link>
          </div>
          {clients.map((item) => {
            const log = item.today_log;
            if (log === null) {
              return null;
            }
            return (
              <div key={item.client.id} className="status-row">
                <Avatar
                  firstName={item.client.first_name}
                  lastName={item.client.last_name}
                />
                <div className="row-main">
                  <div className="row-title">{fullName(item.client)}</div>
                  <div className="row-sub">{describeDay(log)}</div>
                </div>
                <PhaseBadge phase={log.cycle_phase} />
              </div>
            );
          })}
          {notLogged.length > 0 && (
            <p className="row-sub not-logged">
              Not logged today:{" "}
              {notLogged.map((item) => fullName(item.client)).join(", ")}
            </p>
          )}
        </div>
      </div>
    </>
  );
}
