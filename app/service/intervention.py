from enum import Enum
import re
from typing import List, Optional
from .building_metrics import BuildingMetrics

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
        self.theme = theme.strip()

        if stages is None and base_effect is not None:
            self.stages = [Stage("Standalone", base_effect)]
        elif stages and not base_effect:
            self.stages = stages
        else:
            raise ValueError(
                f"Intervention must have either have a non-zero number of stages," 
                f"or a base_effect, but not both. Got: stages={stages}, base_effect={base_effect}"
            )
        
    def apply_metrics(self, bm: BuildingMetrics):
            metrics = bm.get_all_metrics()

            for metric_name, details in metrics.items():
                value = details.get("value")
                scaling_rules = details.get("scaling_rules", {})

                if self.name in scaling_rules:
                    rule = scaling_rules[self.name] 

                    # Parse scaling rule using regex
                    match = re.match(r"([+-]?\d*\.?\d+)% per ([\d.]+)", rule)
                    if match:
                        percent_change = float(match.group(1))  
                        per_unit = float(match.group(2))        

                        multiplier = value / per_unit
                        total_effect = percent_change * multiplier

                        for stage in self.stages:
                            stage.base_effect += total_effect / 100


