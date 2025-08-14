from enum import Enum
from sqlalchemy import ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class ProjectRoleEnum(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"

class ProjectAccess(Base):
    __tablename__ = "project_access"
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[ProjectRoleEnum] = mapped_column(SAEnum(ProjectRoleEnum, name="project_role"), nullable=False)
