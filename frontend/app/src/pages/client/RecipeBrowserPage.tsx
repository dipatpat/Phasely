import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  listRecipes,
  RECIPES_QUERY_KEY,
  searchRecipes,
} from "../../api/library";
import type { MealType, Recipe } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { RecipeDetails } from "../../components/RecipeDetails";
import { MEAL_ORDER } from "../../content/meals";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import { useTodayLog } from "../../hooks/useTodayLog";
import { formatMacros } from "../../utils/format";
import "../trainer/trainer.css";
import "./recipes.css";
import "./today.css";

type Filters = {
  mealType: MealType | null;
  maxCalories: number | null;
  minProtein: number | null;
  dietaryTag: string | null;
};

function optionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

function matchesFilters(recipe: Recipe, filters: Filters): boolean {
  if (filters.mealType && recipe.meal_type !== filters.mealType) return false;
  if (filters.maxCalories !== null && recipe.calories > filters.maxCalories) {
    return false;
  }
  if (
    filters.minProtein !== null &&
    Number(recipe.protein) < filters.minProtein
  ) {
    return false;
  }
  if (
    filters.dietaryTag &&
    !recipe.dietary_tags.some((tag) => tag.name === filters.dietaryTag)
  ) {
    return false;
  }
  return true;
}

export function RecipeBrowserPage() {
  const [text, setText] = useState("");
  const [mealType, setMealType] = useState<MealType | null>(null);
  const [maxCalories, setMaxCalories] = useState("");
  const [minProtein, setMinProtein] = useState("");
  const [dietaryTag, setDietaryTag] = useState("");

  const query = useDebouncedValue(text.trim(), 300);
  const filters: Filters = {
    mealType,
    maxCalories: optionalNumber(maxCalories),
    minProtein: optionalNumber(minProtein),
    dietaryTag: dietaryTag || null,
  };

  const allRecipes = useQuery({
    queryKey: RECIPES_QUERY_KEY,
    queryFn: listRecipes,
  });
  const search = useQuery({
    queryKey: ["recipe-search", query, filters],
    queryFn: () => searchRecipes({ query, ...filters }),
    enabled: query !== "",
    placeholderData: keepPreviousData,
  });
  const todayLog = useTodayLog();

  if (allRecipes.isPending) {
    return <LoadingScreen />;
  }
  if (allRecipes.isError) {
    return <p className="form-error">Could not load recipes.</p>;
  }

  const plannedToday = new Set(
    (todayLog.data?.recommended_recipes ?? []).map((recipe) => recipe.id),
  );
  const tagNames = [
    ...new Set(
      allRecipes.data.flatMap((recipe) =>
        recipe.dietary_tags.map((tag) => tag.name),
      ),
    ),
  ].sort();
  const results =
    query === ""
      ? allRecipes.data
          .filter((recipe) => matchesFilters(recipe, filters))
          .sort((a, b) => a.name.localeCompare(b.name))
      : (search.data ?? []);

  return (
    <>
      <div className="top-bar">
        <h1>Recipes</h1>
      </div>
      <p className="date-tag">
        Search by name, ingredient or tag. Tip: <code>chicken -rice</code>{" "}
        excludes a word, quotes find an exact phrase.
      </p>

      <input
        className="search-input"
        type="search"
        placeholder="Search recipes — e.g. salmon, oats, gluten-free…"
        value={text}
        onChange={(event) => setText(event.target.value)}
      />

      <div className="recipe-filters">
        <div className="filter-chips">
          {([null, ...MEAL_ORDER] as const).map((option) => (
            <button
              key={option ?? "all"}
              type="button"
              className={`filter-chip capitalize${mealType === option ? " active" : ""}`}
              onClick={() => setMealType(option)}
            >
              {option ?? "All meals"}
            </button>
          ))}
        </div>
        <input
          className="form-input"
          type="number"
          min={0}
          placeholder="Max kcal"
          value={maxCalories}
          onChange={(event) => setMaxCalories(event.target.value)}
        />
        <input
          className="form-input"
          type="number"
          min={0}
          placeholder="Min protein (g)"
          value={minProtein}
          onChange={(event) => setMinProtein(event.target.value)}
        />
        <select
          className="form-input"
          value={dietaryTag}
          onChange={(event) => setDietaryTag(event.target.value)}
        >
          <option value="">Any diet</option>
          {tagNames.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>

      <p className="date-tag">
        {query === ""
          ? `${results.length} recipes`
          : `${results.length} results for "${query}" · best matches first`}
        {search.isFetching && " · searching…"}
      </p>
      {search.isError && <p className="form-error">{search.error.message}</p>}

      {results.length === 0 && (
        <div className="card">
          <p className="empty-text">
            No recipes match. Try fewer filters or other words.
          </p>
        </div>
      )}

      <div className="recipe-grid">
        {results.map((recipe) => (
          <details key={recipe.id} className="card recipe-card">
            <summary>
              <div className="recipe-card-top">
                <div>
                  <div className="recipe-name">{recipe.name}</div>
                  <div className="recipe-macros capitalize">
                    {recipe.meal_type}
                  </div>
                </div>
                <span className="macro-pill macro-kcal">
                  {recipe.calories} kcal
                </span>
              </div>
              <div className="recipe-macros">{formatMacros(recipe)}</div>
              {plannedToday.has(recipe.id) && (
                <span className="plan-badge">🌱 In your plan today</span>
              )}
            </summary>
            <RecipeDetails recipe={recipe} />
          </details>
        ))}
      </div>
    </>
  );
}
