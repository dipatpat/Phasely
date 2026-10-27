import type { ReactNode } from "react";
import type { Session } from "../../api/types";
import { formatTime } from "../../utils/dates";
import { fullName } from "../../utils/format";

type SessionRowProps = {
  session: Session;
  showClient: boolean;
  children?: ReactNode;
};

export function SessionRow({ session, showClient, children }: SessionRowProps) {
  const start = new Date(session.scheduled_at);
  return (
    <div className="session-item">
      <div className="session-date-block">
        <div className="session-day-num">{start.getDate()}</div>
        <div className="session-month">
          {start.toLocaleString("en-GB", { month: "short" })}
        </div>
      </div>
      <div className="session-info">
        {showClient && (
          <div className="row-title">{fullName(session.client)}</div>
        )}
        <div className="row-sub">
          {formatTime(start)} · {session.duration_minutes} min
          {session.notes && ` · ${session.notes}`}
        </div>
        {session.status === "cancelled" && session.cancellation_reason && (
          <div className="row-sub">Reason: {session.cancellation_reason}</div>
        )}
      </div>
      <span className={`status-badge badge-${session.status}`}>
        {session.status}
      </span>
      {children && <div className="session-actions">{children}</div>}
    </div>
  );
}
