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

    cause: Mapped[str] = mapped_column(String, nullable=False)  # metric key
    effected_intervention: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )

    # Make these nullable to allow open-ended ranges (your services already support None)
    metric_type: Mapped[MetricTypeEnum | None] = mapped_column(
        SAEnum(MetricTypeEnum, name="metric_type"), nullable=True
    )
    lower_bound: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    multiplier: Mapped[float] = mapped_column(Numeric, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)

    
