"""What a replacement seat already holds in the engine's state that a handover would overwrite.

A handover gives the replacement the leaver's household, works, holdings and institutions as they stand. Cash,
debts and known techniques of the replacement merge with the leaver's (sim/seats/handover_rules.py); anything else it holds
would be lost, so a replacement that holds some is refused. What the seats module keeps (disclosures, dealings, the
goal record) it adds itself.
"""
import dataclasses
from typing import List

from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.materials.state import MaterialsSeat
from sim.polity.state import PolitySeat
from sim.resources.state import ResourcesSeat

STAFF_FIELDS = ("scholars", "artisans", "directors_extra", "slaves", "freedmen", "reserve_craftsmen", "reserve_scholars")
OWED_FIELDS = ("bondage_debt", "interest_arrears")


def holdings_in_use(holdings) -> bool:
	"""Whether the holdings hold anything: a field at its default, or a lazily made container with nothing in it, does not."""
	fresh = HoldingsState()
	for field in dataclasses.fields(holdings):
		value, default = getattr(holdings, field.name), getattr(fresh, field.name)
		if value == default or field.name == "_dashboard_history":
			continue
		if field.name == "_material_stock_opening":
			used = any((value or {}).get("tonnes", {}).values())
		elif field.name == "_material_stock_ledger":
			used = any(value.values()) if value else False
		else:
			used = bool(value) or bool(default)
		if used:
			return True
	return False


def module_state_in_use(state) -> bool:
	"""Whether a module's seat state holds anything: a field at its default, or an empty container where none was made, does not."""
	fresh = type(state)()
	for field in dataclasses.fields(state):
		value, default = getattr(state, field.name), getattr(fresh, field.name)
		if value != default and (bool(value) or bool(default)):
			return True
	return False


def holds_that_would_be_lost(seat) -> List[str]:
	"""What `seat` holds in the engine's state beyond cash, debts and known techniques, named for the player; empty for
	an empty seat."""
	household, projects = seat.household, seat.projects
	found = []
	if projects.active or len(projects.business.entry_keys()):
		found.append("works")
	if any(getattr(household, name, 0) for name in STAFF_FIELDS) or household.employees:
		found.append("staff")
	if any(getattr(household, name, 0) for name in OWED_FIELDS) or household.bondage_years_left:
		found.append("arrears or bondage")
	if (holdings_in_use(seat.holdings) or module_state_in_use(seat.modules.get("resources") or ResourcesSeat())
			or module_state_in_use(seat.modules.get("materials") or MaterialsSeat())):
		found.append("holdings")
	if (seat.modules.get("polity") or PolitySeat()).gov != 0.0:
		found.append("institutions")
	if seat.seat_progress != SeatProgressState():
		found.append("goal record")
	return found
