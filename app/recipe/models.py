from decimal import Decimal

from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, Table, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, TimestampMixin, UUIDMixin
from app.core.enums import MealType

recipe_dietary_tag = Table(
    "recipe_dietary_tag",
    Base.metadata,
    Column("recipe_id", UUID(as_uuid=True), ForeignKey("recipe.id"), primary_key=True),
    Column(
        "dietary_tag_id",
        UUID(as_uuid=True),
        ForeignKey("dietary_tag.id"),
        primary_key=True,
    ),
)


class DietaryTag(UUIDMixin, Base):
    __tablename__ = "dietary_tag"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    recipes: Mapped[list["Recipe"]] = relationship(  # noqa: F821
        secondary=recipe_dietary_tag, back_populates="dietary_tags"
    )


class Recipe(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recipe"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType), nullable=False)
    protein: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    carbs: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    fat: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    serving_size: Mapped[str] = mapped_column(String(100), nullable=False)
    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    dietary_tags: Mapped[list["DietaryTag"]] = relationship(
        secondary=recipe_dietary_tag, back_populates="recipes"
    )
    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class Ingredient(UUIDMixin, Base):
    __tablename__ = "ingredient"

    recipe_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipe.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
