"""What a state's forms take, as shares the taxpayers' own decisions can net out of what they earn.

A farmer weighs the harvest he keeps against the wage; a lessor weighs the rent he keeps against what holding the land
costs him. These read the state's present rates (levers included) and the share of each form's base its officials reach,
so a higher rate lowers the return the actor decides on. Nothing here is a response: the actors' existing rules turn the
lower return into fewer hands on the land or land given up.
"""
from typing import Any

from .revenue_bases import HARVEST_MATERIAL


def harvest_share_taken(world: Any, material: str = HARVEST_MATERIAL) -> float:
	"""Share of the harvest of `material` that the state's forms on the harvest take from growers (in kind or in
	coin), weighted by the tiles each form is levied on and by the share its officials reach; at most all of it."""
	taken = 0.0
	for form in world.revenue_forms():
		if form["basis"] != "harvest" or float(form["rate"]) <= 0.0:
			continue
		if (form.get("paid_in") or material) != material:
			continue
		tiles = form.get("tiles")
		excepted = form.get("except_tiles")
		if tiles is None and excepted is None:
			covered = 1.0
		else:
			chosen = set(tiles) if tiles is not None else set(world.held_tiles())
			covered = world.arable_share(frozenset(chosen - set(excepted or ())))
		taken += float(form["rate"]) * covered * world.collectible_share(None if tiles is None else tiles)
	return min(1.0, taken)


def land_tax_share_of_rent(world: Any) -> float:
	"""Share of a year's rent that the state's forms on land take from the owner: a form on the rent takes its rate;
	a form on the land's value (rent capitalised at the market rate of interest) takes its rate over that rate of
	interest, per year. Weighted by the share of the state's officials reach; at most all of it."""
	rate = world.market_rate()
	taken = 0.0
	for form in world.revenue_forms():
		if float(form["rate"]) <= 0.0:
			continue
		if form["basis"] == "land_rent":
			taken += float(form["rate"])
		elif form["basis"] == "land_value" and rate > 0.0:
			taken += float(form["rate"]) / rate
	return min(1.0, taken * world.collectible_share(None))


def after_tax_rent(rent: float, share_taken: float) -> float:
	"""What an owner keeps of a rent after the state's share."""
	return rent * (1.0 - min(1.0, max(0.0, share_taken)))
