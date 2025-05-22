from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base



class InterventionThemeImpact(Base):
    _tablename_ = 'intervention_theme_impacts'

    id = Column(Integer, primary_key=True)
    intervention_id = Column(Integer, ForeignKey('interventions.id'))
    theme_id = Column(Integer, ForeignKey('themes.id'))
    impact_rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intervention = relationship("Intervention", back_populates="theme_impacts")
    theme = relationship("Theme", back_populates="theme_impacts")
