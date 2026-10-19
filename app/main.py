from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.auth.router import router as auth_router
from app.client.router import router as client_router
from app.core.database import get_db
from app.exercise.router import router as exercise_router
from app.log.router import router as log_router
from app.plan.router import router as plan_router
from app.recipe.router import router as recipe_router
from app.report.router import router as report_router
from app.session.router import router as session_router
from app.shopping.router import router as shopping_router
from app.trainer.router import router as trainer_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(trainer_router)
app.include_router(client_router)
app.include_router(session_router)
app.include_router(exercise_router)
app.include_router(recipe_router)
app.include_router(plan_router)
app.include_router(log_router)
app.include_router(report_router)
app.include_router(shopping_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}
