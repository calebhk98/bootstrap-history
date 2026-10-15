"""What an entrant gives up while its concern ramps to full takings: the entry test counts it."""
from typing import Any, Tuple


def ramp_shortfall(world: Any, node_id: str, gross: float, costs: float) -> Tuple[float, float]:
	"""(takings foregone while ramping, deepest cumulative loss) of a concern founded now whose full-ramp
	takings are `gross` and whose yearly costs are `costs`."""
	foregone, balance, deepest, age = 0.0, 0.0, 0.0, 0
	while True:
		ramp = world.ramp(world.year - age, node_id)
		foregone += gross * (1.0 - ramp)
		balance += gross * ramp - costs
		deepest = max(deepest, -balance)
		if ramp >= 1.0 or age > 1000:
			return foregone, deepest
		age += 1
