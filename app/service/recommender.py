from typing import List
from .system_state import SystemState
from .intervention import Intervention

class Recommender:
    def __init__(self, system_state: SystemState, interventions: List[Intervention]):
        self.state = system_state
        self.interventions = interventions

    def recommend(self, target_theme: str, count: int = 4):
        candidates = []

        for intervention in self.interventions:


            if intervention.name in self.state.implemented_interventions:
                continue
            if intervention.theme != target_theme:
                continue
            if self.state.theme_scores[target_theme] >= self.state.target_scores[target_theme]:
                continue

            
            modifier = self.state.theme_modifiers.get(target_theme, 0)
            score = intervention.stages[0].base_effect * (1 + modifier)
            candidates.append((score, intervention))

        candidates.sort(reverse=True, key=lambda x: x[0]) # Lambda key func sorts tuples by first element (score)



        return [i for _, i in candidates[:count]]

# This should probably read directly from SystemState through a getter, rather than requiring the class to be 
# reinitialised with the new list of intervention in each time this class is needed