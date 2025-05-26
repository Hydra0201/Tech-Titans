from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.service.auth import register_user, login_user
from app.service.project import get_user_projects, create_project
from app.service.building_metrics import get_building_parameters_input, save_building_parameters
from app.models.projects import Project
from app.models.themes import Theme

def project_details_page(db: Session, project: Project):
    """Handle building parameters input"""
    print("\n=== Building Parameters ===")
    params = get_building_parameters_input()
    
    try:
        save_building_parameters(db, project.id, params)
        print("\nBuilding parameters saved!")
        theme_rating_page(db, project)
    except ValueError as e:
        print(f"\nError: {e}")
        if input("Try again? (y/n): ").lower() == 'y':
            project_details_page(db, project)

def theme_rating_page(db: Session, project: Project):
    """Handle theme ratings input (0-100 scale)"""
    from app.service.theme_rating import get_all_themes, save_theme_ratings
    
    print("\n=== SUSTAINABILITY THEME RATING ===")
    print("Rate each theme (0-100, Enter to skip)\n")
    
    themes = get_all_themes(db)
    ratings = {}
    
    for theme in themes:
        while True:
            try:
                rating = input(f"{theme.id}. {theme.name}: ").strip()
                if not rating:
                    ratings[theme.id] = None
                    break
                
                rating = float(rating)
                if 0 <= rating <= 100:
                    ratings[theme.id] = rating
                    break
                print("Please enter between 0-100")
            except ValueError:
                print("Please enter a number")
    
    save_theme_ratings(db, project.id, ratings)
    print("\nTheme ratings saved!")
    # intervention_recommendation_page(db, project)  # Next step

def handle_project_selection(db: Session, user_id: int):
    """Manage project selection menu"""
    projects = get_user_projects(db, user_id)
    if not projects:
        print("\nNo projects found. Create one first.")
        return None
        
    print("\nYour Projects:")
    for i, p in enumerate(projects, 1):
        print(f"{i}. {p.name} ({p.project_type})")
    
    choice = input("\nSelect project (or 'b' to go back): ")
    if choice.lower() == 'b':
        return None
        
    try:
        return projects[int(choice)-1]
    except (ValueError, IndexError):
        print("Invalid selection")
        return None

def handle_new_project(db: Session, user_id: int):
    """Handle new project creation"""
    print("\n=== New Project ===")
    name = input("Project name: ").strip()
    if not name:
        print("Name cannot be empty!")
        return None
        
    return create_project(
        db=db,
        user_id=user_id,
        name=name,
        project_type=input("Project type: ").strip() or None,
        location=input("Location: ").strip() or None,
        building_type=input("Building type: ").strip() or None
    )

def start_app():
    """Main application entry point"""
    init_db()
    db = SessionLocal()
    
    try:
        print("\n=== CarbonBalance ===")
        user = login_user(db) if input("1. Login\n2. Register\nChoose: ") == '1' else register_user(db)
        if not user:
            print("Authentication failed")
            return
            
        while True:
            print("\n=== Main Menu ===")
            choice = input("1. Existing Project\n2. New Project\n3. Exit\nChoose: ")
            
            project = None
            if choice == '1':
                project = handle_project_selection(db, user.id)
            elif choice == '2':
                project = handle_new_project(db, user.id)
                if project:
                    print(f"\nProject '{project.name}' created!")
            elif choice == '3':
                break
                
            if project:
                project_details_page(db, project)
                
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    start_app()