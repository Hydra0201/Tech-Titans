from sqlalchemy.orm import Session
from app.models.themes import Theme  # Corrected import
from app.models.project_themes_ratings import ProjectThemeRating  # Added import

def get_all_themes(db: Session):
    """Get all available sustainability themes"""
    return db.query(Theme).order_by(Theme.id).all()

def save_theme_ratings(db: Session, project_id: int, ratings: dict):
    """Save theme ratings (0-100 scale)"""
    for theme_id, rating in ratings.items():
        if rating is None:
            continue
            
        existing = db.query(ProjectThemeRating).filter(
            ProjectThemeRating.project_id == project_id,
            ProjectThemeRating.theme_id == theme_id
        ).first()
        
        if existing:
            existing.target_rating = rating
        else:
            db.add(ProjectThemeRating(
                project_id=project_id,
                theme_id=theme_id,
                target_rating=rating
            ))
    
    db.commit()