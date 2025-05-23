from app.core.database import engine, Base
from app.models.users import User
from app.models.projects import Project
from app.models.themes import Theme
from app.models.project_interventions import ProjectIntervention
from app.models.project_themes_ratings import ProjectThemeRating
from app.models.project_reports import ProjectReport
from app.models.building_parameters import BuildingParameter
from app.models.intervention_theme_impacts import InterventionThemeImpact
from app.models.interventions import Intervention

# Create all tables
Base.metadata.create_all(bind=engine)
