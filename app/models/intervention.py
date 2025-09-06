# carbonbalance/models/intervention.py
from sqlalchemy import String, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # links to a Theme (int PK)
    theme_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("themes.id", ondelete="RESTRICT"), nullable=False
    )

    # 0–1 (if you clamp in logic); keep Numeric for DB-side precision
    base_effectiveness: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # optional text
    description: Mapped[str | None] = mapped_column(String, nullable=True)
