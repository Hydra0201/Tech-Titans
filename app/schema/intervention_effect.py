#intervention_effect.py
from sqlalchemy import Numeric, Enum as SAEnum, ForeignKey, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .metric_effect import MetricTypeEnum
from ..db.base import Base

class InterventionEffect(Base):
    __tablename__ = "intervention_effects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cause_intervention: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )
    effected_intervention: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )
    metric_type: Mapped[MetricTypeEnum] = mapped_column(SAEnum(MetricTypeEnum, name="metric_type"), nullable=False)
    lower_bound: Mapped[float] = mapped_column(Numeric, nullable=False)
    upper_bound: Mapped[float] = mapped_column(Numeric, nullable=False)
    multiplier: Mapped[float] = mapped_column(Numeric, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("upper_bound > lower_bound", name="ck_int_range_valid"),
        CheckConstraint("multiplier > 0", name="ck_int_multiplier_positive"),
    )