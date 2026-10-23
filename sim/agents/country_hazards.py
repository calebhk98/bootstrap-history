"""What a country's own declared hazards take from its output: the war and its aftermath its civilisation file dates."""
from typing import Any, Dict, List

OUTPUT_FACTOR_KEY = "output_factor"


def output_factor(hazards: List[Dict[str, Any]], year: float) -> float:
	"""Share of its output a country keeps in `year`: the lowest `output_factor` of the declared hazards whose years include it
	(one when none runs). A country has no works of the founder's to hold the floor up, so a hazard's own figure stands."""
	running = [float(hazard[OUTPUT_FACTOR_KEY]) for hazard in hazards
			   if OUTPUT_FACTOR_KEY in hazard and hazard.get("years") and hazard["years"][0] <= year <= hazard["years"][-1]]
	return min(running + [1.0])
