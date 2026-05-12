from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, UUIDMixin


class DietaryTag(UUIDMixin, Base):
    __tablename__ = "dietary_tag"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    recipes: Mapped[list["Recipe"]] = relationship(  # noqa: F821
        secondary="recipe_dietary_tag", back_populates="dietary_tags"
    )
