# carbonbalance/models/stage.py
from sqlalchemy import Integer, ForeignKey, String, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Stage(Base):
    __tablename__ = "stages"

    src_intervention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )
    dst_intervention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False
    )
    # keep it TEXT to align with Supabase SQL; values 'prereq' | 'mutex'
    relation_type: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("src_intervention_id", "dst_intervention_id", "relation_type", name="pk_stages"),
    )
