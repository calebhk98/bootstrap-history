"""Bridge entries the production module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached."""
from sim.production.api import BumpHouseholdVersion

from .bridge import bridge_command, bridge_view


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
