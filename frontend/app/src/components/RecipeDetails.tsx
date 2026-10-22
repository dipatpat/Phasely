import type { Recipe } from "../api/types";

export function RecipeDetails({ recipe }: { recipe: Recipe }) {
  return (
    <div className="recipe-details">
      <p className="recipe-serving">Serving: {recipe.serving_size}</p>

      {recipe.dietary_tags.length > 0 && (
        <div className="tag-list">
          {recipe.dietary_tags.map((tag) => (
            <span key={tag.id} className="tag-chip">
              {tag.name}
            </span>
          ))}
        </div>
      )}

      <ul className="ingredient-list">
        {recipe.ingredients.map((ingredient) => (
          <li key={ingredient.id}>
            {Number(ingredient.quantity)} {ingredient.unit} {ingredient.name}
          </li>
        ))}
      </ul>

      {recipe.preparation_notes && (
        <p className="recipe-notes">{recipe.preparation_notes}</p>
      )}
    </div>
  );
}
