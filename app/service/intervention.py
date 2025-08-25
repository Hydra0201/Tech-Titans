from enum import Enum
from typing import List, Optional


class Stage:
    def __init__(self, name: str, base_effect: float):
        self.name = name
        self.base_effect = base_effect


class Intervention:
    def __init__(
        self, 
        name: str, 
        theme: str, 
        stages: Optional[List[Stage]] = None, # list of Stage objects, or defaults to None
        base_effect: Optional[float] = None
    ): 
        self.name = name
        self.theme = theme

        if stages is None and base_effect is not None:
            self.stages = [Stage("Standalone", base_effect)]
        elif stages and not base_effect:
            self.stages = stages
        else:
            raise ValueError(
                f"Intervention must have either have a non-zero number of stages," 
                f"or a base_effect, but not both. Got: stages={stages}, base_effect={base_effect}"
            )


    # TODO: Write a function which loads interventions from JSON and instantiates corresponding intervention objects
    
def recommend_interventions_for_theme(theme_name: str, target: float, dependencies: list):
    """
    Recommend a list of interventions that help achieve the given target score for a theme.
    Selects interventions whose total effect is closest to the target without exceeding it.
    """
    # Filter interventions that positively impact the theme
    options = [
        dep for dep in dependencies
        if dep["target_theme"] == theme_name and dep["effect_percentage"] > 0
    ]

    # Sort by strongest effect first
    options.sort(key=lambda x: x["effect_percentage"], reverse=True)

    total = 0
    selected = []

    for option in options:
        effect = option["effect_percentage"]
        if total + effect <= target:
            selected.append(option)
            total += effect

    return selected, total
