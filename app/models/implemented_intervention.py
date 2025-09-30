# carbonbalance/models/implemented_intervention.py
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base

class ImplementedIntervention(Base):
    __tablename__ = "implemented_interventions"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    impl_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    implemented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
