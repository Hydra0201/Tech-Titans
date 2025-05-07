from enum import Enum
from typing import List, Optional


class InterventionTheme(Enum):
    def __init__(self, name: str):
        # TODO: Implement (read themes from JSON/DB)
        pass

class Stage:
    def __init__(self, name: str, base_effect: float):
        self.name = name
        self.base_effect = base_effect


class Intervention:
    def __init__(
        self, 
        name: str, 
        theme: InterventionTheme, 
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
    
