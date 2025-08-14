# carbonbalance/models/recommendation.py
from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint, CheckConstraint, Sequence
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base

recommendation_id_seq = Sequence("recommendation_id_seq", metadata=Base.metadata)

class Recommendation(Base):
    __tablename__ = "recommendations"

    # batch id you assign to all 3 rows of the same snapshot
    recommendation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, server_default=recommendation_id_seq.next_value()
    )
    intervention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="RESTRICT"), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    final_effectiveness: Mapped[float] = mapped_column(Numeric(6,4), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint("recommendation_id", "rank", name="uq_rec_rank_per_batch"),
        CheckConstraint("final_effectiveness >= 0 AND final_effectiveness <= 1", name="ck_final_eff_0_1"),
    )
