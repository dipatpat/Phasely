import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  deleteRecipe,
  listRecipes,
  RECIPES_QUERY_KEY,
} from "../../api/library";
import type { MealType, Recipe } from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { MEAL_ORDER } from "../../content/meals";
import { formatMacros } from "../../utils/format";
import { RecipeFormModal } from "./RecipeFormModal";
import "./library.css";
import "./trainer.css";
import "../client/today.css";

export function RecipeLibraryPage() {
  const queryClient = useQueryClient();
  const recipes = useQuery({
    queryKey: RECIPES_QUERY_KEY,
    queryFn: listRecipes,
  });
  const [search, setSearch] = useState("");
  const [mealFilter, setMealFilter] = useState<MealType | "all">("all");
  const [editing, setEditing] = useState<Recipe | "new" | null>(null);

  const remove = useMutation({
    mutationFn: (id: string) => deleteRecipe(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: RECIPES_QUERY_KEY }),
  });

  if (recipes.isPending) {
    return <LoadingScreen />;
  }
  if (recipes.isError) {
    return <p className="form-error">Could not load recipes.</p>;
  }

  function handleDelete(recipe: Recipe) {
    if (window.confirm(`Delete "${recipe.name}"? This cannot be undone.`)) {
      remove.mutate(recipe.id);
    }
  }

  const term = search.trim().toLowerCase();
  const visible = recipes.data
    .filter((recipe) => recipe.name.toLowerCase().includes(term))
    .filter((recipe) => mealFilter === "all" || recipe.meal_type === mealFilter)
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <div className="top-bar">
        <h1>Recipe library</h1>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setEditing("new")}
        >
          + New recipe
        </button>
      </div>

      <div className="client-filters">
        <input
          className="form-input client-search"
          placeholder="🔍 Search recipes"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="filter-chips">
          {(["all", ...MEAL_ORDER] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={
                mealFilter === option ? "filter-chip active" : "filter-chip"
              }
              onClick={() => setMealFilter(option)}
            >
              {option === "all" ? "All" : option}
            </button>
          ))}
        </div>
      </div>

      <p className="date-tag">
        {visible.length} of {recipes.data.length} recipes
      </p>
      {remove.error && <p className="form-error">{remove.error.message}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Recipe</th>
              <th>Meal</th>
              <th>Macros</th>
              <th>Kcal</th>
              <th>Tags</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {visible.map((recipe) => (
              <tr key={recipe.id}>
                <td>
                  <strong>{recipe.name}</strong>
                  <div className="row-sub">
                    {recipe.ingredients.length} ingredients ·{" "}
                    {recipe.serving_size}
                  </div>
                </td>
                <td className="capitalize">{recipe.meal_type}</td>
                <td>{formatMacros(recipe)}</td>
                <td>{recipe.calories}</td>
                <td>
                  <div className="tag-list">
                    {recipe.dietary_tags.map((tag) => (
                      <span key={tag.id} className="tag-chip">
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="table-actions">
                  <button
                    type="button"
                    className="btn-cancel btn-small"
                    onClick={() => setEditing(recipe)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn-danger btn-small"
                    onClick={() => handleDelete(recipe)}
                    disabled={remove.isPending}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing !== null && (
        <RecipeFormModal
          recipe={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
