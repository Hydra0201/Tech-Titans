from sqlalchemy.orm import Session
from app.models.projects import Project  # Import the Project class, not the module

def get_user_projects(db: Session, user_id: int):
    """Get all projects for a user"""
    return db.query(Project).filter(Project.user_id == user_id).order_by(Project.updated_at.desc()).all()

def create_project(
    db: Session,
    user_id: int,
    name: str,
    project_type: str = None,
    location: str = None,
    building_type: str = None
):
    """Create a new project"""
    project = Project(
        name=name,
        user_id=user_id,
        project_type=project_type,
        location=location,
        building_type=building_type
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project