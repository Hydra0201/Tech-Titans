from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:87654321@localhost:5432/carbonbalance"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base first
Base = declarative_base()

def init_db():
    # Import all models AFTER Base is created
    from app.models.users import User
    from app.models.projects import Project
    from app.models.themes import Theme
    from app.models.project_interventions import ProjectIntervention
    from app.models.project_themes_ratings import ProjectThemeRating
    from app.models.project_reports import ProjectReport
    from app.models.building_parameters import BuildingParameter
    from app.models.intervention_theme_impacts import InterventionThemeImpact
    from app.models.interventions import Intervention
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from .import_data import import_themes, import_interventions
        import_themes(db)
        import_interventions(db)
    finally:
        db.close()