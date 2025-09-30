# carbonbalance/models/config.py
from sqlalchemy import Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Config(Base):
    __tablename__ = "config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    step_size: Mapped[float] = mapped_column(Numeric, nullable=False)
