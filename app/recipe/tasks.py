import asyncio
import uuid

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from app.celery import celery_app
from app.core.config import settings
from app.recipe.models import Recipe

task_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TaskSessionLocal = async_sessionmaker(task_engine, expire_on_commit=False)


@celery_app.task(name="sync_recipe_to_postgres_full_text_search")
def sync_recipe_to_postgres_full_text_search(recipe_id: str) -> None:
    return asyncio.run(_sync_recipe_to_postgres_full_text_search(recipe_id))


async def _sync_recipe_to_postgres_full_text_search(recipe_id: str) -> None:
    recipe_uuid = uuid.UUID(recipe_id)
    async with TaskSessionLocal() as db:
        result = await db.execute(
            select(Recipe)
            .options(selectinload(Recipe.dietary_tags))
            .where(Recipe.id == recipe_uuid)
        )
        recipe = result.scalar_one_or_none()
        if recipe is None:
            return

        tag_text = " ".join(tag.name for tag in recipe.dietary_tags)
        vector = (
            func.setweight(func.to_tsvector("english", recipe.name), text("'A'"))
            .op("||")(
                func.setweight(func.to_tsvector("english", tag_text), text("'B'"))
            )
            .op("||")(
                func.setweight(
                    func.to_tsvector("english", recipe.meal_type.value), text("'C'")
                )
            )
        )
        await db.execute(
            update(Recipe).where(Recipe.id == recipe_uuid).values(search_vector=vector)
        )
        await db.commit()
