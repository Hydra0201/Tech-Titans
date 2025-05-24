import json


with open ('data/base_effectiveness.json', 'r') as f:
    be_data = json.load(f)


class SystemState:
    def __init__(self):
        self.implemented_interventions = []  
        self.theme_modifiers = {}
        self.theme_scores = {} # Current score for each theme
        self.target_scores = {} # User's target score for each theme (0.0 where not targeted)

    def initialise_themes(self, be_data): # initialises the dict items for every theme, key is theme name, value is initially 0.0
        themes = {entry["description"] for entry in be_data}
        self.theme_modifiers = {name: 0.0 for name in themes}
        self.theme_scores = {name: 0.0 for name in themes}
        self.target_scores = {name: 0.0 for name in themes}

    def apply_intervention(self, Intervention, dependencies): # Implements an intervention, calculating the new theme_score for relevant theme
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
        for theme, modifier in self.theme_modifiers.items():
            self.theme_scores[theme] += Intervention.stages[0].base_effect * (1 + modifier)

    def update_target_scores(self, new_target_scores: dict):
        for key in new_target_scores:
            if key in self.target_scores:
                self.target_scores[key] = new_target_scores[key]

# This class concerns things which change as the program executes:
    # List of interventions chosen so far
    # Dictionary or similar containing themes and their current modifier and score
    


# NOTE: theme_scores are increased by implementing an intervention which affects that theme. Currently, we are 
# increasing this score by the intervention's base_effect * the multiplier. For this to work, we really need to
# think about how we are determining the theme_scores.