from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class BuildingParameter(Base):
    __tablename__ = 'building_parameters'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    external_wall_area = Column(Float)
    building_footprint = Column(Float)
    facade_opening_percentage = Column(Float)
    wall_floor_ratio = Column(Float)
    footprint_gifa = Column(Float)
    gifa = Column(Float)
    external_openings = Column(Float)
    number_of_levels = Column(Integer)
    average_height_per_level = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("app.models.projects.Project", back_populates="building_parameters")
