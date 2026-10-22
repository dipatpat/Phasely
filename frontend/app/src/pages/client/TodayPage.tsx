import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { RecipeDetails } from "../../components/RecipeDetails";
import { getTodayLog, todayLogQueryKey } from "../../api/dailyLog";
import type {
  DailyLogWithRecommendations,
  MealType,
  Recipe,
  TrainingPlanExercise,
} from "../../api/types";
import { useAuth } from "../../auth/useAuth";
import { LoadingScreen } from "../../components/LoadingScreen";
import { energyOptionFor } from "../../content/energy";
import { PHASE_INFO } from "../../content/phases";
import { formatLongDate, greeting, todayIso } from "../../utils/dates";
import { formatMacros, formatPrescription } from "../../utils/format";
import { DailyLogModal } from "./DailyLogModal";
import "./today.css";

const MEAL_ORDER: MealType[] = ["breakfast", "lunch", "dinner", "snack"];

export function TodayPage() {
  const { user } = useAuth();
  const todayLog = useQuery({
    queryKey: todayLogQueryKey(todayIso()),
    queryFn: getTodayLog,
  });
  const [isLogOpen, setIsLogOpen] = useState(false);

  if (todayLog.isPending) {
    return <LoadingScreen />;
  }
  if (todayLog.isError) {
    return (
      <p className="form-error">
        Could not load today: {todayLog.error.message}
      </p>
    );
  }

  const log = todayLog.data;
  const now = new Date();

  return (
    <>
      <div className="top-bar">
        <h1>
          {greeting(now)}, {user?.first_name} 👋
        </h1>
      </div>
      <p className="date-tag">{formatLongDate(now)}</p>

      {log ? <PhaseHero log={log} /> : <EmptyHero />}

      {log ? (
        <LoggedBanner log={log} />
      ) : (
        <div className="log-banner">
          <p className="log-banner-text">
            <strong>Log today's data</strong> — your phase, sleep and energy
            decide today's meals and workout.
          </p>
          <button
            type="button"
            className="btn-log"
            onClick={() => setIsLogOpen(true)}
          >
            Log today
          </button>
        </div>
      )}

      <div className="grid-2">
        <MealsCard recipes={log ? log.recommended_recipes : null} />
        <WorkoutCard exercises={log ? log.recommended_exercises : null} />
      </div>

      {isLogOpen && <DailyLogModal onClose={() => setIsLogOpen(false)} />}
    </>
  );
}

function PhaseHero({ log }: { log: DailyLogWithRecommendations }) {
  const phase = log.daily_log.cycle_phase;
  const info = PHASE_INFO[phase];
  return (
    <div className={`phase-hero hero-${phase}`}>
      <div className="phase-left">
        <div className="phase-icon">{info.icon}</div>
        <div>
          <div className="phase-label">Today's phase</div>
          <div className="phase-name">{info.label} phase</div>
          <div className="phase-sub">{info.summary}</div>
        </div>
      </div>
      <div className="phase-traits">
        {info.traits.map((trait) => (
          <span key={trait} className="trait-chip">
            {trait}
          </span>
        ))}
      </div>
    </div>
  );
}

function EmptyHero() {
  return (
    <div className="phase-hero hero-empty">
      <div className="phase-left">
        <div className="phase-icon">❔</div>
        <div>
          <div className="phase-label">Today's phase</div>
          <div className="phase-name">Not logged yet</div>
          <div className="phase-sub">
            Log your day to see your phase and recommendations.
          </div>
        </div>
      </div>
    </div>
  );
}

function LoggedBanner({ log }: { log: DailyLogWithRecommendations }) {
  const { hours_of_sleep, energy_level } = log.daily_log;
  const energy = energy_level === null ? null : energyOptionFor(energy_level);
  return (
    <div className="log-banner">
      <p className="log-banner-text">
        <strong>Today is logged ✓</strong>
        {hours_of_sleep !== null && ` · ${Number(hours_of_sleep)} h sleep`}
        {energy && ` · energy ${energy.emoji} ${energy.label}`}
      </p>
    </div>
  );
}

function MealsCard({ recipes }: { recipes: Recipe[] | null }) {
  return (
    <div className="card">
      <div className="card-title">Today's meals</div>
      {recipes === null && (
        <p className="empty-text">Log today to see your meals.</p>
      )}
      {recipes !== null && recipes.length === 0 && (
        <p className="empty-text">
          Your trainer hasn't planned meals for this phase yet.
        </p>
      )}
      {MEAL_ORDER.map((mealType) => {
        const meals = (recipes ?? []).filter(
          (recipe) => recipe.meal_type === mealType,
        );
        if (meals.length === 0) {
          return null;
        }
        return (
          <div key={mealType} className="meal-section">
            <div className="meal-type-label">{mealType}</div>
            {meals.map((recipe, index) => (
              <details key={`${recipe.id}-${index}`} className="recipe-item">
                <summary>
                  <div>
                    <div className="recipe-name">{recipe.name}</div>
                    <div className="recipe-macros">{formatMacros(recipe)}</div>
                  </div>
                  <span className="macro-pill macro-kcal">
                    {recipe.calories} kcal
                  </span>
                </summary>
                <RecipeDetails recipe={recipe} />
              </details>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function WorkoutCard({
  exercises,
}: {
  exercises: TrainingPlanExercise[] | null;
}) {
  return (
    <div className="card">
      <div className="card-title">Today's workout</div>
      {exercises === null && (
        <p className="empty-text">Log today to see your workout.</p>
      )}
      {exercises !== null && exercises.length === 0 && (
        <p className="empty-text">
          Nothing planned for today at your energy level — a rest day.
        </p>
      )}
      {exercises?.map((item) => (
        <details key={item.exercise.id} className="exercise-item">
          <summary>
            <div>
              <div className="exercise-name">{item.exercise.name}</div>
              <div className="exercise-params">{formatPrescription(item)}</div>
            </div>
            {item.difficulty_level && (
              <span className={`difficulty-chip diff-${item.difficulty_level}`}>
                {item.difficulty_level}
              </span>
            )}
          </summary>
          {item.exercise.description && (
            <p className="exercise-description">{item.exercise.description}</p>
          )}
        </details>
      ))}
    </div>
  );
}
