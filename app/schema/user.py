from enum import Enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base

class RoleEnum(str, Enum):
    Admin = "Admin"
    Employee = "Employee"
    Client = "Client"
    Consultant = "Consultant"

class AccessLevelEnum(str, Enum):
    viewer = "viewer"
    editor = "editor"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Use shared enum type names to match other tables / SQL scripts
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role"),
        nullable=False,
        default=RoleEnum.Client,   # client-side default; your route sends role explicitly anyway
    )

    default_access_level: Mapped[AccessLevelEnum] = mapped_column(
        SAEnum(AccessLevelEnum, name="access_level"),
        nullable=False,
        default=AccessLevelEnum.viewer,  # client-side default; your route sends it explicitly
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
