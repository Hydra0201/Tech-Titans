from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Intervention(Base):
    __tablename__ = 'interventions'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme_impacts = relationship("app.models.intervention_theme_impacts.InterventionThemeImpact", back_populates="intervention")
    project_interventions = relationship("app.models.project_interventions.ProjectIntervention", back_populates="intervention")
