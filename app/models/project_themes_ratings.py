from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base



class ProjectThemeRating(Base):
    __tablename__ = 'project_theme_ratings'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    theme_id = Column(Integer, ForeignKey('themes.id'))
    target_rating = Column(Float)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("app.models.projects.Project", back_populates="theme_ratings")
    theme = relationship("app.models.themes.Theme", back_populates="theme_ratings")
