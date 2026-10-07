import uuid
from datetime import date

from pydantic import BaseModel, field_validator

from app.core.enums import CyclePhase


class DailyBreakdownEntry(BaseModel):
    date: date
    cycle_phase: CyclePhase | None
    energy_level: int | None
    hours_of_sleep: float | None
    calories_consumed: int
    exercises_completed: int


class WeeklyReportPublic(BaseModel):
    week_start: date
    week_end: date
    daily_breakdown: list[DailyBreakdownEntry]


class WeeklyReportGenerate(BaseModel):
    week_start: date
    client_id: uuid.UUID | None = None

    @field_validator("week_start")
    @classmethod
    def week_start_must_be_monday(cls, value: date) -> date:
        if value.isoweekday() != 1:
            raise ValueError("week_start must be a Monday")
        return value
