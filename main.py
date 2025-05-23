import json
from service import building_metrics as bm
from service import intervention as iv
from service import system_state as ss
from data import be

interventions = [] # List of Intervention objects

with open ('data/base_effectiveness.json', 'r') as f:
    be_data = json.load(f)

for d in be_data:
    name = d["intervention"]
    base_effect = d["base_effectiveness"]
    theme = d["description"]

    interventions.append(iv.Intervention(name, theme, base_effect=base_effect)) # Appends Intervention objects to interventions[]
    # TODO: Implement stages




