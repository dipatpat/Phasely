from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import app.client.models
import app.exercise.models
import app.log.models
import app.plan.models
import app.recipe.models
import app.session.models
import app.trainer.models
import app.user.models
from app.auth.router import router as auth_router
from app.client.router import router as client_router
from app.core.database import get_db
from app.trainer.router import router as trainer_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(trainer_router)
app.include_router(client_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}
