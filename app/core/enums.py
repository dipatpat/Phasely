import enum


class UserRole(enum.Enum):
    trainer = "trainer"
    client = "client"


class CyclePhase(enum.Enum):
    menstrual = "menstrual"
    follicular = "follicular"
    ovulatory = "ovulatory"
    luteal = "luteal"


class MealType(enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
