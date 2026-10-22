import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { createMealLog, listMealLogs, mealLogsQueryKey } from "../../api/logs";
import type { MealType, Recipe } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { Modal } from "../../components/Modal";
import { MEAL_ORDER } from "../../content/meals";
import { PHASE_INFO } from "../../content/phases";
import { useTodayLog } from "../../hooks/useTodayLog";
import { formatLongDate, todayIso } from "../../utils/dates";
import { formatMacros, macrosFor, sumMacros } from "../../utils/format";
import "./logging.css";
import "./today.css";

type MealToLog = {
  recipe: Recipe;
  mealType: MealType;
};

export function MealsPage() {
  const today = todayIso();
  const todayLog = useTodayLog();
  const mealLogs = useQuery({
    queryKey: mealLogsQueryKey(today),
    queryFn: () => listMealLogs(today),
  });
  const [mealToLog, setMealToLog] = useState<MealToLog | null>(null);

  if (todayLog.isPending || mealLogs.isPending) {
    return <LoadingScreen />;
  }
  if (todayLog.isError || mealLogs.isError) {
    return <p className="form-error">Could not load your meals.</p>;
  }

  const log = todayLog.data;
  const logs = mealLogs.data;
  const totals = sumMacros(
    logs.map((entry) =>
      macrosFor(entry.recipe, Number(entry.portion_quantity)),
    ),
  );
  const stats = [
    { label: "Calories", value: totals.calories, unit: "kcal" },
    { label: "Protein", value: totals.protein, unit: "g" },
    { label: "Carbs", value: totals.carbs, unit: "g" },
    { label: "Fat", value: totals.fat, unit: "g" },
  ];

  return (
    <>
      <div className="top-bar">
        <h1>Meal log</h1>
      </div>
      <p className="date-tag">
        {formatLongDate(new Date())}
        {log && ` · ${PHASE_INFO[log.daily_log.cycle_phase].label} phase`}
      </p>

      <div className="stats">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <div className="stat-label">{stat.label} today</div>
            <div className="stat-value">
              {stat.value}
              <span className="stat-unit">{stat.unit}</span>
            </div>
          </div>
        ))}
      </div>

      {log === null ? (
        <div className="card">
          <p className="empty-text">
            Log your day on the <Link to="/client">Today</Link> page first —
            your cycle phase decides which meals are planned for you.
          </p>
        </div>
      ) : (
        MEAL_ORDER.map((mealType) => {
          const planned = log.recommended_recipes.filter(
            (recipe) => recipe.meal_type === mealType,
          );
          if (planned.length === 0) {
            return null;
          }
          return (
            <div key={mealType} className="card log-section">
              <div className="card-title">{mealType}</div>
              {planned.map((recipe, index) => {
                const servings = logs
                  .filter(
                    (entry) =>
                      entry.recipe.id === recipe.id &&
                      entry.meal_type === mealType,
                  )
                  .reduce(
                    (sum, entry) => sum + Number(entry.portion_quantity),
                    0,
                  );
                return (
                  <div key={`${recipe.id}-${index}`} className="log-row">
                    <div>
                      <div className="recipe-name">{recipe.name}</div>
                      <div className="recipe-macros">
                        {formatMacros(recipe)} · {recipe.calories} kcal per
                        serving
                      </div>
                      {servings > 0 && (
                        <div className="logged-note">
                          ✓ Logged: {servings} serving
                          {servings === 1 ? "" : "s"}
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      className={servings > 0 ? "btn-cancel" : "btn-primary"}
                      onClick={() => setMealToLog({ recipe, mealType })}
                    >
                      {servings > 0 ? "Log again" : "Log"}
                    </button>
                  </div>
                );
              })}
            </div>
          );
        })
      )}

      {mealToLog && (
        <LogMealModal
          recipe={mealToLog.recipe}
          mealType={mealToLog.mealType}
          onClose={() => setMealToLog(null)}
        />
      )}
    </>
  );
}

type LogMealModalProps = {
  recipe: Recipe;
  mealType: MealType;
  onClose: () => void;
};

function LogMealModal({ recipe, mealType, onClose }: LogMealModalProps) {
  const queryClient = useQueryClient();
  const [servings, setServings] = useState("1");
  const preview = macrosFor(recipe, Number(servings) || 0);

  const saveMeal = useMutation({
    mutationFn: () =>
      createMealLog({
        recipe_id: recipe.id,
        meal_type: mealType,
        consumed_at: new Date().toISOString(),
        portion_quantity: Number(servings),
        portion_unit: "serving",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mealLogsQueryKey(todayIso()) });
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveMeal.mutate();
  }

  return (
    <Modal title={`Log ${recipe.name}`} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="servings">Servings eaten</label>
          <input
            id="servings"
            className="form-input"
            type="number"
            min={0.25}
            max={10}
            step={0.25}
            value={servings}
            onChange={(event) => setServings(event.target.value)}
            required
          />
          <p className="hint">1 serving = {recipe.serving_size}</p>
        </div>
        <p className="macro-preview">
          {preview.calories} kcal · P {preview.protein} g · C {preview.carbs} g
          · F {preview.fat} g
        </p>
        {saveMeal.error && (
          <p className="form-error">{saveMeal.error.message}</p>
        )}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-save"
            disabled={saveMeal.isPending}
          >
            {saveMeal.isPending ? "Saving…" : "Save meal"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
