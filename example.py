from service.intervention import Intervention
from service.system_state import SystemState
from service.recommender import Recommender
from service.building_metrics import BuildingMetrics
import json

# Truncation helper (improves readibility, some intervention names are very long)
def truncate(text, max_length=60):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."


# Load interventions
with open("data/base_effectiveness.json", "r") as f:
    be_data = json.load(f)

interventions = []
for item in be_data:
    name = item.get("intervention")
    theme = item.get("description")
    base_effect = item.get("base_effectiveness")

    if base_effect is None:
        print(f"Skipping {name}: base_effectiveness missing")
        continue

    interventions.append(Intervention(name, theme, base_effect=base_effect))

# Prompt user for target scores
themes = sorted(set(i.theme.strip() for i in interventions))
target_scores = {}

print("\nEnter target score (e.g., 1.5) for each theme, or press Enter to skip:")
for theme in themes:
    raw = input(f"{theme}: ").strip()
    try:
        target_scores[theme] = float(raw) if raw else 0.0
    except ValueError:
        print("Invalid input. Defaulting to 0.")
        target_scores[theme] = 0.0


metrics = BuildingMetrics()
with open("data/building_metrics.json", "r") as f:
    bm_data = json.load(f)
metrics.read_metrics(bm_data)

for i in interventions:
    i.apply_metrics(metrics)


state = SystemState()
state.initialise_themes(be_data)
state.update_target_scores(target_scores)

# Recommender loop
while True:
    # Collect all themes that are still below target
    themes_below_target = [
        theme for theme in target_scores
        if state.theme_scores[theme] < target_scores[theme]
    ]

    if not themes_below_target:
        print("\nAll themes have reached their targets. You're done!")
        break

    # Recommend interventions
    recommender = Recommender(state, interventions)
    candidates = []

    for theme in themes_below_target:
        recs = recommender.recommend(theme)
        for r in recs:
            if r not in candidates:
                candidates.append(r)

    if not candidates:
        print("No more interventions to recommend.")
        break

    print("\nTop intervention candidates:")
    for idx, intervention in enumerate(candidates[:4], start=1):
        theme = intervention.theme
        effect = intervention.stages[0].base_effect
        candidate_display = (f"{idx}. {intervention.name} ({theme}) — +{effect:.2f}")
        print(truncate(candidate_display))

    choice = input("\nSelect an intervention to implement (1-4), or press Enter to quit: ").strip()
    if not choice:
        break

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(candidates[:4]):
            selected = candidates[choice_idx]
            print(truncate(f"\nApplying: {selected.name}"), 40)
            state.apply_intervention(selected, [])
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a number.")
