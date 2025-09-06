from sqlalchemy import ForeignKey, Numeric, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class ProjectThemeScore(Base):
    __tablename__ = "project_theme_scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    theme_id: Mapped[int] = mapped_column(Integer, ForeignKey("themes.id"))
    raw_weight: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    normalized_weight: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "theme_id", name="uq_pts_proj_theme"),
    )
