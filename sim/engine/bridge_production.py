"""Bridge entries the production module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached."""
from sim.assembly.api import QUOTE
from sim.production.api import BumpHouseholdVersion

from .bridge import bridge_command, bridge_view
from .data import calculated_goods_prices


@bridge_view("held_goods_prices_in_hours", kind=QUOTE)
def held_goods_prices_in_hours(sim, held):
	"""{material: labour-hour price} of every material the solver prices when the techniques `held` are known, at the
	farming the civilisation opens with (one solve per set)."""
	return calculated_goods_prices(held, civilization_id=sim.civ.get("id"), civilization=sim.civ, money_per_labour_hour=1.0)


@bridge_view("projects_operating", seat_scoped=True)
def projects_operating(sim):
	"""The acting seat's concerns and capabilities that are open (the live set: the engine adds and discards in place)."""
	return sim.state.projects.operating


@bridge_view("running_versions", seat_scoped=True)
def running_versions(sim):
	"""(changes of what the acting seat has done, of what it has open, of the sizes of its institutions): what a memo over them is keyed by."""
	household = sim.household
	return household.done_version, household.operating_version, household.institution_units_version


@bridge_command(BumpHouseholdVersion)
def bump_household_version(sim, command):
	"""Count one change on the acting household's `done` or `operating` counter."""
	if command.counter == "done":
		sim.household.bump_done_version()
	else:
		sim.household.bump_operating_version()
