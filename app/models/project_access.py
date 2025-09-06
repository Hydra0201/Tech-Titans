# app/models/project_access.py
from sqlalchemy import ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base
from .user import AccessLevelEnum  # reuse viewer|editor enum

class ProjectAccess(Base):
    __tablename__ = "project_access"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    access_level: Mapped[AccessLevelEnum] = mapped_column(
        SAEnum(AccessLevelEnum, name="access_level"),
        nullable=False
    )
