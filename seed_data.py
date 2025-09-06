import json
from app.models.theme import Theme 
from app.models.intervention import Intervention
from app.db import SessionLocal  

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def seed_data():
    db = SessionLocal()
    try:
        themes = load_json('data/theme.json')
        for theme in themes:
            db.add(Theme(**theme))

        interventions = load_json('data/intervention.json')
        for intervention in interventions:
            db.add(Intervention(**intervention))

        db.commit()
    finally:
        db.close()

if __name__ == '__main__':
    seed_data()
