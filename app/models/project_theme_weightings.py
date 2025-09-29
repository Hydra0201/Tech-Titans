# app/models/project_theme_weighting.py
from sqlalchemy import Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class ProjectThemeWeighting(Base):
    __tablename__ = "project_theme_weightings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    theme_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("themes.id", ondelete="CASCADE"),
        nullable=False,
    )

    weight_raw: Mapped[float]  = mapped_column(Float, nullable=False)
    weight_norm: Mapped[float] = mapped_column(Float, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("project_id", "theme_id", name="uq_ptw_proj_theme"),
    )
