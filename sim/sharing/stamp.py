"""The stamp a shared answer is confirmed by: what the owners' changes make stale, read as views."""
from typing import Any, Optional

from .rules import Stamp


def _people_and_techniques(needs: Any) -> tuple:
	"""What changes the year, the techniques in force, the operating set, forest, nitre, mines and the people."""
	return (needs.year(), needs.techniques_version(), needs.operating_version(), len(needs.techniques_held()), len(needs.operating()),
	        needs.forest_hectares(), needs.nitre_beds()["square_metres"], needs.population().total, needs.real_output_per_head(),
	        len(needs.mine_workings()))


def view_stamp(needs: Any) -> Optional[Stamp]:
	"""The stamp for answers shared inside a view's scope; None when the world has no demand table to compare."""
	demand = needs.material_demand_held()
	if demand is None:
		return None
	return ((needs.material_prices(), demand), (needs.others_trade_stamp(),) + _people_and_techniques(needs))


def standalone_stamp(needs: Any) -> Stamp:
	"""The stamp for an answer shared outside a view: it leaves out the prices and the year's trade, which such an answer
	does not read."""
	return ((), _people_and_techniques(needs))
