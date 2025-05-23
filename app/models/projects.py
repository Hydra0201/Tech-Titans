from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    project_type = Column(String)
    location = Column(String)
    building_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("app.models.users.User", back_populates="projects")
    building_parameters = relationship("app.models.building_parameters.BuildingParameter", back_populates="project", uselist=False)
    theme_ratings = relationship("app.models.project_themes_ratings.ProjectThemeRating", back_populates="project")
    interventions = relationship("app.models.project_interventions.ProjectIntervention", back_populates="project")
    reports = relationship("app.models.project_reports.ProjectReport", back_populates="project")
