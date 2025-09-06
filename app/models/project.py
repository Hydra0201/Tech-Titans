from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    project_type: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    building_type: Mapped[str | None] = mapped_column(String, nullable=True)
    
    levels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    external_wall_area: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    footprint_area: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    opening_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    wall_to_floor_ratio: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    footprint_gifa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gifa_total: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    external_openings_area: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    avg_height_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # add explicit types
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
