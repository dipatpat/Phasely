import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";
import { listRecipes, RECIPES_QUERY_KEY } from "../../api/library";
import {
  addNutritionAssignment,
  archiveNutritionPlan,
  clientPlanQueryKey,
  createNutritionPlan,
  getClientNutritionPlan,
  removeNutritionAssignment,
} from "../../api/plans";

import { CLIENT_OVERVIEW_QUERY_KEY, getClient } from "../../api/trainer";
import type {
  CyclePhase,
  MealType,
  NutritionPlan,
  NutritionPlanRecipe,
} from "../../api/types";
import { LoadingScreen } from "../../components/LoadingScreen";
import { MEAL_ORDER } from "../../content/meals";
import { countByPhase, PHASE_INFO } from "../../content/phases";
import { formatMacros, fullName } from "../../utils/format";
import { PhaseTabs } from "./PhaseTabs";
import "../client/logging.css";
import "../client/today.css";
import "./library.css";
import "./plans.css";
import "./trainer.css";

export function NutritionPlanPage() {
  const { clientId = "" } = useParams();
  const queryClient = useQueryClient();
  const planKey = clientPlanQueryKey("nutrition", clientId);

  const client = useQuery({
    queryKey: ["client", clientId],
    queryFn: () => getClient(clientId),
  });
  const plan = useQuery({
    queryKey: planKey,
    queryFn: () => getClientNutritionPlan(clientId),
  });
  const recipes = useQuery({
    queryKey: RECIPES_QUERY_KEY,
    queryFn: listRecipes,
  });

  const [phase, setPhase] = useState<CyclePhase>("menstrual");
  const [title, setTitle] = useState("Cycle-synced nutrition");
  const [recipeId, setRecipeId] = useState("");
  const [mealType, setMealType] = useState<MealType>("breakfast");

  function showPlan(updated: NutritionPlan) {
    queryClient.setQueryData(planKey, updated);
  }

  const create = useMutation({
    mutationFn: () => createNutritionPlan(clientId, title.trim()),
    onSuccess: (created) => {
      showPlan(created);
      queryClient.invalidateQueries({ queryKey: CLIENT_OVERVIEW_QUERY_KEY });
    },
  });
  const add = useMutation({
    mutationFn: (planId: string) =>
      addNutritionAssignment(planId, {
        recipe_id: recipeId,
        meal_type: mealType,
        cycle_phase: phase,
      }),
    onSuccess: (updated) => {
      showPlan(updated);
      setRecipeId("");
    },
  });
  const remove = useMutation({
    mutationFn: ({
      planId,
      item,
    }: {
      planId: string;
      item: NutritionPlanRecipe;
    }) =>
      removeNutritionAssignment(planId, {
        recipe_id: item.recipe.id,
        meal_type: item.meal_type,
        cycle_phase: item.cycle_phase,
      }),
    onSuccess: showPlan,
  });

  const archive = useMutation({
    mutationFn: (planId: string) => archiveNutritionPlan(planId),
    onSuccess: () => {
      queryClient.setQueryData(planKey, null);
      queryClient.invalidateQueries({ queryKey: CLIENT_OVERVIEW_QUERY_KEY });
    },
  });

  if (client.isPending || plan.isPending || recipes.isPending) {
    return <LoadingScreen />;
  }
  if (client.isError || plan.isError || recipes.isError) {
    return <p className="form-error">Could not load the nutrition plan.</p>;
  }

  const current = plan.data;
  const name = fullName(client.data);
  const header = (
    <>
      <Link className="back-link" to={`/trainer/clients/${clientId}`}>
        ← Back to {name}
      </Link>
      <div className="top-bar">
        <h1>Nutrition plan</h1>
        {current && (
          <button
            type="button"
            className="btn-danger btn-small"
            disabled={archive.isPending}
            onClick={() => {
              if (
                window.confirm(
                  `Archive "${current.title}"? ${name} will have no nutrition plan until you create a new one. The old plan is kept as history.`,
                )
              ) {
                archive.mutate(current.id);
              }
            }}
          >
            Archive plan
          </button>
        )}
      </div>
      {archive.error && <p className="form-error">{archive.error.message}</p>}

      <p className="date-tag">
        {name}
        {current && ` · ${current.title}`}
      </p>
    </>
  );

  if (current === null) {
    return (
      <>
        {header}
        <form
          className="card create-plan"
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
        >
          <p className="empty-text">{name} has no active nutrition plan yet.</p>
          <div className="form-group">
            <label htmlFor="plan-title">Plan title</label>
            <input
              id="plan-title"
              className="form-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
            />
          </div>
          {create.error && <p className="form-error">{create.error.message}</p>}
          <button
            type="submit"
            className="btn-primary"
            disabled={create.isPending}
          >
            Create plan
          </button>
        </form>
      </>
    );
  }

  const sortedRecipes = [...recipes.data].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  const inPhase = current.recipes.filter((item) => item.cycle_phase === phase);

  return (
    <>
      {header}
      <PhaseTabs
        selected={phase}
        counts={countByPhase(current.recipes)}
        onSelect={setPhase}
      />

      <form
        className="card add-card"
        onSubmit={(event) => {
          event.preventDefault();
          add.mutate(current.id);
        }}
      >
        <div className="card-title">
          Add a recipe to the {PHASE_INFO[phase].label.toLowerCase()} phase
        </div>
        <div className="add-fields">
          <select
            className="form-input"
            value={recipeId}
            onChange={(event) => setRecipeId(event.target.value)}
            required
          >
            <option value="">Choose a recipe…</option>
            {sortedRecipes.map((recipe) => (
              <option key={recipe.id} value={recipe.id}>
                {recipe.name} ({recipe.calories} kcal)
              </option>
            ))}
          </select>
          <select
            className="form-input capitalize"
            value={mealType}
            onChange={(event) => setMealType(event.target.value as MealType)}
          >
            {MEAL_ORDER.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="btn-primary"
            disabled={add.isPending}
          >
            Add
          </button>
        </div>
        {add.error && <p className="form-error">{add.error.message}</p>}
      </form>

      {remove.error && <p className="form-error">{remove.error.message}</p>}
      <div className="grid-2">
        {MEAL_ORDER.map((meal) => {
          const items = inPhase.filter((item) => item.meal_type === meal);
          return (
            <div key={meal} className="card">
              <div className="card-title">{meal}</div>
              {items.length === 0 && (
                <p className="empty-text">Nothing planned.</p>
              )}
              {items.map((item) => (
                <div key={item.recipe.id} className="log-row">
                  <div>
                    <div className="recipe-name">{item.recipe.name}</div>
                    <div className="recipe-macros">
                      {formatMacros(item.recipe)} · {item.recipe.calories} kcal
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn-danger btn-small"
                    aria-label={`Remove ${item.recipe.name}`}
                    disabled={remove.isPending}
                    onClick={() => remove.mutate({ planId: current.id, item })}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      <p className="hint">
        Several recipes for the same meal are alternatives: the client sees all
        of them, and the shopping list rotates them day by day.
      </p>
    </>
  );
}
