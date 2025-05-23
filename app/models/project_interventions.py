from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ProjectIntervention(Base):
    __tablename__ = 'project_interventions'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    intervention_id = Column(Integer, ForeignKey('interventions.id'))
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("app.models.projects.Project", back_populates="interventions")
    intervention = relationship("app.models.interventions.Intervention", back_populates="project_interventions")
