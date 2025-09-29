# carbonbalance/models/runtime_score.py
from sqlalchemy import Numeric, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class RuntimeScore(Base):
    __tablename__ = "runtime_scores"
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    intervention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), primary_key=True
    )

    adjusted_base_effectiveness: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    theme_weighted_effectiveness: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
