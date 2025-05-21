import json


with open ('data/base_effectiveness.json', 'r') as f:
    be_data = json.load(f)


class SystemState:
    def __init__(self):
        self.implemented_interventions = []  
        self.theme_modifiers = {}
        self.theme_scores = {}

    def initialise_themes(self, be_data): # initialises the dict items for every theme, key is theme name, value is initially 0.0
        themes = {entry["description"] for entry in be_data}
        self.theme_modifiers = {name: 0.0 for name in themes}
        self.theme_scores = {name: 0.0 for name in themes}

    def apply_intervention(self, Intervention, dependencies):
        self.implemented_interventions.append(Intervention.name)

        for dep in dependencies:
            if dep["source_intervention"] == Intervention.name:
                theme = dep["target_theme"]
                effect = dep["effect_percentage"]

                if theme not in self.theme_modifiers:
                    raise ValueError(
                        f"Unknown theme '{theme}' in dependency for intervention '{Intervention.name}'"
                    )

                self.theme_modifiers[theme] += effect / 100.0

        # No theme check should happen here, since we may never have matched anything
        for theme, modifier in self.theme_modifiers.items():
            self.theme_scores[theme] += Intervention.stages[0].base_effect * (1 + modifier)


# This class concerns things which change as the program executes:
    # List of interventions chosen so far
    # Dictionary or similar containing themes and their current modifier and score
    