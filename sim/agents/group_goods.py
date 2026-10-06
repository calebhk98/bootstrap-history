"""The society's own producers of a goods category as interest groups: the strata whose trades make it."""
from typing import Any, Dict, List

from .sector import Sector
from .stratum_year import own_income
from .group_strata import organisable
from .tuning_strata import STRATUM_WORKING_SHARE


def goods_sectors(strata: List[Any], categories: Dict[str, Dict[str, Any]], world: Any) -> List[Sector]:
	"""For each category whose price the founder's and the firms' concerns depress, the strata that
	make it: each trade's income, shared out over the categories it works in by `trade_weights`,
	loses the price depression."""
	sectors = []
	for category, data in sorted(categories.items()):
		depression = float(data.get("price_depression") or 0.0)
		weights = data.get("trade_weights") or {}
		if depression <= 0.0:
			continue
		income = people = 0.0
		for stratum in strata:
			trade = stratum.record.plan.get("trade")
			weight = float(weights.get(trade) or 0.0)
			if not organisable(stratum) or weight <= 0.0:
				continue
			income += weight * own_income(stratum, world)
			people += weight * stratum.record.members * float(stratum.record.plan.get("work_share", STRATUM_WORKING_SHARE))
		if income <= 0.0:
			continue
		sectors.append(Sector(
			"displaced_producers", category, "producers of " + category,
			"the concerns you and the firms run have pushed the price of %s down %d%%" % (
				category, round(100.0 * depression)),
			income * depression, income, people, 1.0))
		# the founder answers for his share of the sellers; firms and states selling into the category answer for the rest
		sectors[-1].blame_share = float(data.get("founder_share", 1.0))
	return sectors
