from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Theme(Base):
    __tablename__ = 'themes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme_ratings = relationship("app.models.project_themes_ratings.ProjectThemeRating", back_populates="theme")
    theme_impacts = relationship("app.models.intervention_theme_impacts.InterventionThemeImpact", back_populates="theme")
