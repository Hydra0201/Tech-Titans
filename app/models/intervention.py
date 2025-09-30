# carbonbalance/models/intervention.py
from sqlalchemy import String, ForeignKey, Numeric, Integer, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    theme_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("themes.id", ondelete="RESTRICT"), nullable=False
    )

    base_effectiveness: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # NEW: matches manual SQL
    cost_weight: Mapped[float] = mapped_column(Numeric, nullable=False, server_default=text("1.0"))
    is_stage: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
