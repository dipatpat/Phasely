import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getShoppingList } from "../../api/reports";
import { LoadingScreen } from "../../components/LoadingScreen";
import { PhaseBadge } from "../../components/PhaseBadge";
import { formatDayLabel, formatWeekday, weekStartIso } from "../../utils/dates";
import "../trainer/trainer.css";
import "./progress.css";

const WEEKS = [
  { label: "This week", start: weekStartIso(0) },
  { label: "Next week", start: weekStartIso(-1) },
];

export function ShoppingListPage() {
  const [weekStart, setWeekStart] = useState(WEEKS[0].start);
  const [checked, setChecked] = useState<Set<string>>(new Set());

  const list = useQuery({
    queryKey: ["shopping-list", weekStart],
    queryFn: () => getShoppingList(weekStart),
  });

  function toggle(key: string) {
    const next = new Set(checked);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setChecked(next);
  }

  if (list.isPending) {
    return <LoadingScreen />;
  }
  if (list.isError) {
    return <p className="form-error">{list.error.message}</p>;
  }

  const { days, items, unpredictable_dates: unpredictable } = list.data;

  return (
    <>
      <div className="top-bar">
        <h1>Shopping list</h1>
        <button
          type="button"
          className="btn-cancel btn-small no-print"
          onClick={() => window.print()}
        >
          Print
        </button>
      </div>
      <p className="date-tag">
        {formatDayLabel(list.data.week_start)} –{" "}
        {formatDayLabel(list.data.week_end)} · based on your logged and
        predicted cycle phases
      </p>

      <div className="filter-chips week-chips no-print">
        {WEEKS.map((week) => (
          <button
            key={week.start}
            type="button"
            className={
              week.start === weekStart ? "filter-chip active" : "filter-chip"
            }
            onClick={() => {
              setWeekStart(week.start);
              setChecked(new Set());
            }}
          >
            {week.label}
          </button>
        ))}
      </div>

      <div className="week-strip">
        {days.map((day) => (
          <div key={day.date} className="week-day">
            <div className="week-day-name">{formatWeekday(day.date)}</div>
            <PhaseBadge phase={day.cycle_phase} />
            {day.meals.map((meal) => (
              <div key={meal.meal_type} className="week-day-meal">
                {meal.recipe_name}
              </div>
            ))}
          </div>
        ))}
      </div>

      {unpredictable.length > 0 && (
        <p className="form-error">
          No cycle data for {unpredictable.length} day(s), so their meals aren't
          included. Log your period start to improve the prediction.
        </p>
      )}

      <div className="card">
        <div className="card-title">
          Ingredients · {checked.size}/{items.length} in the basket
        </div>
        {items.length === 0 && (
          <p className="empty-text">
            Nothing to buy: no meals are planned for this week.
          </p>
        )}
        {items.map((item) => {
          const key = `${item.ingredient}|${item.unit}`;
          const isDone = checked.has(key);
          return (
            <label
              key={key}
              className={isDone ? "shopping-item done" : "shopping-item"}
            >
              <input
                type="checkbox"
                checked={isDone}
                onChange={() => toggle(key)}
              />
              <span>{item.ingredient}</span>
              <span className="shopping-qty">
                {Number(item.quantity)} {item.unit}
              </span>
            </label>
          );
        })}
      </div>
    </>
  );
}
