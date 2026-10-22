import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";
import {
  CLIENT_OVERVIEW_QUERY_KEY,
  getClientOverview,
} from "../../api/trainer";
import type { ClientOverview, CyclePhase } from "../../api/types";
import { Avatar } from "../../components/Avatar";
import { LoadingScreen } from "../../components/LoadingScreen";
import { PhaseBadge } from "../../components/PhaseBadge";
import { PHASE_INFO, PHASES } from "../../content/phases";
import { formatRelativeDay } from "../../utils/dates";
import { describeDay, fullName } from "../../utils/format";
import "./trainer.css";

type PhaseFilter = CyclePhase | "all" | "none";

const FILTERS: { value: PhaseFilter; label: string }[] = [
  { value: "all", label: "All" },
  ...PHASES.map((phase) => ({ value: phase, label: PHASE_INFO[phase].label })),
  { value: "none", label: "Not logged" },
];

export function ClientsPage() {
  const overview = useQuery({
    queryKey: CLIENT_OVERVIEW_QUERY_KEY,
    queryFn: getClientOverview,
  });
  const [search, setSearch] = useState("");
  const [phaseFilter, setPhaseFilter] = useState<PhaseFilter>("all");

  if (overview.isPending) {
    return <LoadingScreen />;
  }
  if (overview.isError) {
    return <p className="form-error">Could not load your clients.</p>;
  }

  const term = search.trim().toLowerCase();
  const visible = overview.data.filter((item) => {
    const phase = item.today_log ? item.today_log.cycle_phase : null;
    const matchesName = fullName(item.client).toLowerCase().includes(term);
    const matchesPhase =
      phaseFilter === "all" ||
      (phaseFilter === "none" ? phase === null : phase === phaseFilter);
    return matchesName && matchesPhase;
  });

  return (
    <>
      <div className="top-bar">
        <h1>Clients</h1>
      </div>

      <div className="client-filters">
        <input
          className="form-input client-search"
          placeholder="🔍 Search by name"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="filter-chips">
          {FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              className={
                phaseFilter === filter.value
                  ? "filter-chip active"
                  : "filter-chip"
              }
              onClick={() => setPhaseFilter(filter.value)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <p className="date-tag">
        Showing {visible.length} of {overview.data.length} clients · phases are
        from today's logs
      </p>

      {visible.length === 0 && (
        <div className="card">
          <p className="empty-text">No clients match your search.</p>
        </div>
      )}

      <div className="client-grid">
        {visible.map((item) => (
          <ClientCard key={item.client.id} item={item} />
        ))}
      </div>
    </>
  );
}

function ClientCard({ item }: { item: ClientOverview }) {
  const { client, today_log: log } = item;
  return (
    <div className="card client-card">
      <div className="client-card-header">
        <Avatar firstName={client.first_name} lastName={client.last_name} />
        <div className="client-card-name">
          <strong>{fullName(client)}</strong>
          <span>🎯 {client.fitness_goal ?? "No goal set"}</span>
        </div>
        <PhaseBadge phase={log ? log.cycle_phase : null} />
      </div>
      <p className="row-sub">
        📅 Last logged:{" "}
        {item.last_log_date ? formatRelativeDay(item.last_log_date) : "never"}
      </p>
      {log && <p className="row-sub">{describeDay(log)}</p>}
      <div className="plan-flags">
        <span
          className={
            item.has_nutrition_plan ? "plan-flag" : "plan-flag missing"
          }
        >
          {item.has_nutrition_plan ? "Nutrition plan" : "No nutrition plan"}
        </span>
        <span
          className={item.has_training_plan ? "plan-flag" : "plan-flag missing"}
        >
          {item.has_training_plan ? "Training plan" : "No training plan"}
        </span>
      </div>
      <Link
        className="btn-primary client-card-link"
        to={`/trainer/clients/${client.id}`}
      >
        View client
      </Link>
    </div>
  );
}
