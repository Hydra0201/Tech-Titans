from enum import Enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base

class RoleEnum(str, Enum):
    Admin = "Admin"
    Contributor = "Contributor"
    Viewer = "Viewer"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum, name="role"), nullable=False, default=RoleEnum.Viewer)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    #  add explicit typing + DateTime column type
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
