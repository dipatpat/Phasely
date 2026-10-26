import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type ChangeEvent, type FormEvent } from "react";
import {
  createRecipe,
  RECIPES_QUERY_KEY,
  updateRecipe,
  type RecipeData,
} from "../../api/library";
import type { MealType, Recipe } from "../../api/types";
import { Modal } from "../../components/Modal";
import { MEAL_ORDER } from "../../content/meals";

type IngredientRow = {
  name: string;
  quantity: string;
  unit: string;
};

type RecipeForm = {
  name: string;
  meal_type: MealType;
  protein: string;
  carbs: string;
  fat: string;
  calories: string;
  serving_size: string;
  preparation_notes: string;
  tags: string;
  ingredients: IngredientRow[];
};

type TextField = Exclude<keyof RecipeForm, "ingredients">;
type FieldElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

const EMPTY_INGREDIENT: IngredientRow = { name: "", quantity: "", unit: "g" };

function toForm(recipe: Recipe | null): RecipeForm {
  if (recipe === null) {
    return {
      name: "",
      meal_type: "breakfast",
      protein: "",
      carbs: "",
      fat: "",
      calories: "",
      serving_size: "1 serving",
      preparation_notes: "",
      tags: "",
      ingredients: [EMPTY_INGREDIENT],
    };
  }
  return {
    name: recipe.name,
    meal_type: recipe.meal_type,
    protein: String(Number(recipe.protein)),
    carbs: String(Number(recipe.carbs)),
    fat: String(Number(recipe.fat)),
    calories: String(recipe.calories),
    serving_size: recipe.serving_size,
    preparation_notes: recipe.preparation_notes ?? "",
    tags: recipe.dietary_tags.map((tag) => tag.name).join(", "),
    ingredients: recipe.ingredients.map((ingredient) => ({
      name: ingredient.name,
      quantity: String(Number(ingredient.quantity)),
      unit: ingredient.unit,
    })),
  };
}

function toData(form: RecipeForm): RecipeData {
  return {
    name: form.name.trim(),
    meal_type: form.meal_type,
    protein: Number(form.protein),
    carbs: Number(form.carbs),
    fat: Number(form.fat),
    calories: Number(form.calories),
    serving_size: form.serving_size.trim(),
    preparation_notes: form.preparation_notes.trim() || null,
    ingredients: form.ingredients
      .filter((row) => row.name.trim() !== "")
      .map((row) => ({
        name: row.name.trim().toLowerCase(),
        quantity: Number(row.quantity),
        unit: row.unit.trim(),
      })),
    dietary_tag_names: form.tags
      .split(",")
      .map((tag) => tag.trim().toLowerCase())
      .filter((tag) => tag !== ""),
  };
}

type RecipeFormModalProps = {
  recipe: Recipe | null;
  onClose: () => void;
};

export function RecipeFormModal({ recipe, onClose }: RecipeFormModalProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<RecipeForm>(() => toForm(recipe));

  const save = useMutation({
    mutationFn: () =>
      recipe
        ? updateRecipe(recipe.id, toData(form))
        : createRecipe(toData(form)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RECIPES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["plan"] });
      onClose();
    },
  });

  function update(field: TextField) {
    return (event: ChangeEvent<FieldElement>) =>
      setForm({ ...form, [field]: event.target.value });
  }

  function updateIngredient(
    index: number,
    field: keyof IngredientRow,
    value: string,
  ) {
    setForm({
      ...form,
      ingredients: form.ingredients.map((row, i) =>
        i === index ? { ...row, [field]: value } : row,
      ),
    });
  }

  function addIngredient() {
    setForm({ ...form, ingredients: [...form.ingredients, EMPTY_INGREDIENT] });
  }

  function removeIngredient(index: number) {
    setForm({
      ...form,
      ingredients: form.ingredients.filter((_, i) => i !== index),
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <Modal title={recipe ? "Edit recipe" : "New recipe"} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              className="form-input"
              value={form.name}
              onChange={update("name")}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="meal_type">Meal type</label>
            <select
              id="meal_type"
              className="form-input capitalize"
              value={form.meal_type}
              onChange={update("meal_type")}
            >
              {MEAL_ORDER.map((mealType) => (
                <option key={mealType} value={mealType}>
                  {mealType}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row-4 form-group">
          {(
            [
              ["protein", "Protein (g)"],
              ["carbs", "Carbs (g)"],
              ["fat", "Fat (g)"],
              ["calories", "Kcal"],
            ] as const
          ).map(([field, label]) => (
            <div key={field}>
              <label htmlFor={field}>{label}</label>
              <input
                id={field}
                className="form-input"
                type="number"
                min={0}
                step={field === "calories" ? 1 : 0.1}
                value={form[field]}
                onChange={update(field)}
                required
              />
            </div>
          ))}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="serving_size">Serving size</label>
            <input
              id="serving_size"
              className="form-input"
              value={form.serving_size}
              onChange={update("serving_size")}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="tags">Dietary tags (comma-separated)</label>
            <input
              id="tags"
              className="form-input"
              placeholder="vegan, gluten-free"
              value={form.tags}
              onChange={update("tags")}
            />
          </div>
        </div>

        <div className="form-group">
          <span className="field-label">Ingredients</span>
          {form.ingredients.map((row, index) => (
            <div key={index} className="ingredient-row">
              <input
                className="form-input"
                placeholder="Ingredient"
                value={row.name}
                onChange={(event) =>
                  updateIngredient(index, "name", event.target.value)
                }
              />
              <input
                className="form-input"
                type="number"
                min={0}
                step={0.1}
                placeholder="Qty"
                value={row.quantity}
                onChange={(event) =>
                  updateIngredient(index, "quantity", event.target.value)
                }
                required={row.name.trim() !== ""}
              />
              <input
                className="form-input"
                placeholder="Unit"
                value={row.unit}
                onChange={(event) =>
                  updateIngredient(index, "unit", event.target.value)
                }
              />
              <button
                type="button"
                className="btn-danger btn-small"
                onClick={() => removeIngredient(index)}
                aria-label="Remove ingredient"
              >
                ✕
              </button>
            </div>
          ))}
          <button type="button" className="btn-link" onClick={addIngredient}>
            + Add ingredient
          </button>
        </div>

        <div className="form-group">
          <label htmlFor="preparation_notes">
            Preparation (one step per line)
          </label>
          <textarea
            id="preparation_notes"
            className="form-input"
            rows={4}
            placeholder={"1. …\n2. …"}
            value={form.preparation_notes}
            onChange={update("preparation_notes")}
          />
        </div>

        {save.error && <p className="form-error">{save.error.message}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn-save" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save recipe"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
