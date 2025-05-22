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

    user = relationship("User", back_populates="projects")
    building_parameters = relationship("BuildingParameter", back_populates="project", uselist=False)
    theme_ratings = relationship("ProjectThemeRating", back_populates="project")
    interventions = relationship("ProjectIntervention", back_populates="project")
    reports = relationship("ProjectReport", back_populates="project")
