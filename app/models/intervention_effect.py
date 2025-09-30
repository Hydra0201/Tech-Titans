from sqlalchemy import Numeric, Enum as SAEnum, ForeignKey, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .metric_effect import MetricTypeEnum  # reuse enum name "metric_type"
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

    metric_type: Mapped[MetricTypeEnum | None] = mapped_column(
        SAEnum(MetricTypeEnum, name="metric_type"), nullable=True
    )
    lower_bound: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    multiplier: Mapped[float] = mapped_column(Numeric, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)

    