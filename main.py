from app.core.database import SessionLocal
from app.models.projects import Project
from app.models.building_parameters import BuildingParameter
from datetime import datetime

def create_project():
    db = SessionLocal()

    try:
        print("=== Create New Project ===")
        name = input("Project Name: ")
        project_type = input("Project Type: ")
        location = input("Location: ")
        building_type = input("Building Type: ")
        user_id = 1  # Replace with actual user logic

        project = Project(
            name=name,
            project_type=project_type,
            location=location,
            building_type=building_type,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        print("\n=== Enter Building Parameters ===")
        params = BuildingParameter(
            project_id=project.id,
            external_wall_area=float(input("External Wall Area (m²): ")),
            building_footprint=float(input("Building Footprint (m²): ")),
            facade_opening_percentage=float(input("Façade Opening %: ")),
            wall_floor_ratio=float(input("Wall:Floor Ratio: ")),
            footprint_gifa=float(input("Footprint:GIFA Ratio: ")),
            gifa=float(input("GIFA (m²): ")),
            external_openings=float(input("External Openings (m²): ")),
            number_of_levels=int(input("Number of Levels: ")),
            average_height_per_level=float(input("Average Height per Level (m): ")),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(params)
        db.commit()

        print("\n✅ Project and Building Parameters Saved!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_project()

