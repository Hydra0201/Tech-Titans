from enum import Enum
from sqlalchemy import String, Numeric, Enum as SAEnum, ForeignKey, CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class MetricTypeEnum(str, Enum):
    ratio = "ratio"
    percentage = "percentage"

class MetricEffect(Base):
    __tablename__ = "metric_effects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cause: Mapped[str] = mapped_column(String, nullable=False)  # metric key (e.g. 'WFR', 'OpeningPct')
    effected_intervention: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )
    metric_type: Mapped[MetricTypeEnum] = mapped_column(SAEnum(MetricTypeEnum, name="metric_type"), nullable=False)
    lower_bound: Mapped[float] = mapped_column(Numeric, nullable=False)
    upper_bound: Mapped[float] = mapped_column(Numeric, nullable=False)
    multiplier: Mapped[float] = mapped_column(Numeric, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("upper_bound > lower_bound", name="ck_range_valid"),
        CheckConstraint("multiplier > 0", name="ck_multiplier_positive"),
    )
