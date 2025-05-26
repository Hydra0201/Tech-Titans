from sqlalchemy.orm import Session
from app.models.building_parameters import BuildingParameter

def get_building_parameters_input():
    """Collect building parameters from user input"""
    print("\n=== Building Parameters Input ===")
    print("Enter building details \n")
    
    def get_input(prompt, input_type=float):
        while True:
            val = input(prompt).strip()
            if not val:
                return None
            try:
                return input_type(val)
            except ValueError:
                print(f"Please enter a valid {input_type.__name__} or leave blank")

    return {
        'external_wall_area': get_input("External wall area (m²): "),
        'building_footprint': get_input("Building footprint (m²): "),
        'facade_opening_percentage': get_input("Façade opening % (0-100): "),
        'wall_floor_ratio': get_input("Wall:Floor ratio: "),
        'footprint_gifa': get_input("Footprint:GIFA ratio: "),
        'gifa': get_input("GIFA (m²): "),
        'external_openings': get_input("External openings count: ", int),
        'number_of_levels': get_input("Number of levels: ", int),
        'average_height_per_level': get_input("Average height/level (m): ")
    }

def save_building_parameters(db: Session, project_id: int, params: dict):
    """Save building parameters to database"""
    # Input validation
    if 'facade_opening_percentage' in params and params['facade_opening_percentage']:
        if not 0 <= params['facade_opening_percentage'] <= 100:
            raise ValueError("Facade opening must be between 0-100%")
    
    # Filter out None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Handle existing parameters
    existing = db.query(BuildingParameter).filter(
        BuildingParameter.project_id == project_id
    ).first()
    
    if existing:
        # Update existing record
        for key, value in params.items():
            setattr(existing, key, value)
    else:
        # Create new record
        params['project_id'] = project_id
        new_params = BuildingParameter(**params)
        db.add(new_params)
    
    db.commit()
    return True