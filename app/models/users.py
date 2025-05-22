from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    _tablename_ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="user")


class Project(Base):
    _tablename_ = 'projects'

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


class BuildingParameter(Base):
    _tablename_ = 'building_parameters'

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

    project = relationship("Project", back_populates="building_parameters")


class Theme(Base):
    _tablename_ = 'themes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme_ratings = relationship("ProjectThemeRating", back_populates="theme")
    theme_impacts = relationship("InterventionThemeImpact", back_populates="theme")


class ProjectThemeRating(Base):
    _tablename_ = 'project_theme_ratings'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    theme_id = Column(Integer, ForeignKey('themes.id'))
    target_rating = Column(Float)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="theme_ratings")
    theme = relationship("Theme", back_populates="theme_ratings")


class Intervention(Base):
    _tablename_ = 'interventions'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme_impacts = relationship("InterventionThemeImpact", back_populates="intervention")
    project_interventions = relationship("ProjectIntervention", back_populates="intervention")


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


class ProjectIntervention(Base):
    _tablename_ = 'project_interventions'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    intervention_id = Column(Integer, ForeignKey('interventions.id'))
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="interventions")
    intervention = relationship("Intervention", back_populates="project_interventions")


class ProjectReport(Base):
    _tablename_ = 'project_reports'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    report_data = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="reports")
