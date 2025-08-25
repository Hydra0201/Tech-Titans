from datetime import datetime
import json
import os
from app.models.intervention_theme_impacts import InterventionThemeImpact
from sqlalchemy.orm import Session
from app.models.themes import Theme
from app.models.interventions import Intervention

def import_themes(db: Session):
    """
    Import themes from JSON file into database
    """
    try:
        # Get the absolute path to Theme.json
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, "data", "Theme.json")
        
        # Check if themes already exist
        if db.query(Theme).count() > 0:
            #print("Themes already exist in database. Skipping import.")
            return False
        
        # Load JSON data
        with open(json_path, 'r') as file:
            themes_data = json.load(file)
        
        # Import themes
        themes = [
            Theme(
                name=item["Themes"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for item in themes_data
        ]
        
        db.bulk_save_objects(themes)
        db.commit()
        #print(f"Successfully imported {len(themes)} themes from {json_path}")
        return True
    
    except FileNotFoundError:
        #print(f"Theme file not found at: {json_path}")
        return False
    except json.JSONDecodeError:
        #print(f" Invalid JSON format in theme file at: {json_path}")
        return False
    except Exception as e:
        db.rollback()
        #print(f" Error importing themes: {str(e)}")
        return False
    
def import_interventions(db: Session):
    """
    Import interventions from JSON file into database
    """
    try:
        # Get the absolute path to Intervention.json
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, "data", "Intervention.json")
        
        # Check if interventions already exist
        if db.query(Intervention).count() > 0:
            #print("Interventions already exist in database. Skipping import.")
            return False
        
        # Load JSON data
        with open(json_path, 'r') as file:
            interventions_data = json.load(file)
        
        # Import interventions
        interventions = [
            Intervention(
                name=item["Interventions"],
                description=item["Intervention Description"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for item in interventions_data
        ]
        
        db.bulk_save_objects(interventions)
        db.commit()
        #print(f"Successfully imported {len(interventions)} interventions from {json_path}")
        return True
    
    except FileNotFoundError:
        #print(f" Intervention file not found at: {json_path}")
        return False
    except json.JSONDecodeError:
        #print(f" Invalid JSON format in intervention file at: {json_path}")
        return False
    except Exception as e:
        db.rollback()
        #print(f" Error importing interventions: {str(e)}")
        return False 

def import_intervention_dependencies(db: Session):
    """
    Import themes from JSON file into database
    """
    try:
        # Get the absolute path to Theme.json
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, "data", "intervention_dependencies.json")
        
        # Check if themes already exist
        if db.query(InterventionThemeImpact).count() > 0:
            #print("Themes already exist in database. Skipping import.")
            return False
        
        # Load JSON data
        with open(json_path, 'r') as file:
            themes_data = json.load(file)
        
        # Import themes
        themes = [
            Theme(
                name=item["Themes"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for item in themes_data
        ]
        
        db.bulk_save_objects(themes)
        db.commit()
        #print(f"Successfully imported {len(themes)} themes from {json_path}")
        return True
    
    except FileNotFoundError:
        #print(f"Theme file not found at: {json_path}")
        return False
    except json.JSONDecodeError:
        #print(f" Invalid JSON format in theme file at: {json_path}")
        return False
    except Exception as e:
        db.rollback()
        #print(f" Error importing themes: {str(e)}")
        return False