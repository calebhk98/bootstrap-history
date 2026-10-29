"""What a replacement seat already holds in the engine's state that a handover would overwrite.

A handover gives the replacement the leaver's household, works, holdings and institutions as they stand. Cash,
debts and known techniques of the replacement merge with the leaver's (sim/seats/handover_rules.py); anything else it holds
would be lost, so a replacement that holds some is refused. What the seats module keeps (disclosures, dealings, the
goal record) it adds itself.
"""
import dataclasses
from typing import List

from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.finance.api import FinanceSeat
from sim.ledger.api import LedgerSeat
from sim.materials.state import MaterialsSeat
from sim.polity.state import PolitySeat
from sim.resources.state import ResourcesSeat
from sim.workforce.api import WorkforceSeat

STAFF_FIELDS = ("scholars", "artisans", "directors_extra", "slaves", "freedmen", "reserve_craftsmen", "reserve_scholars")   # of the workforce slot
OWED_FIELDS = ("bondage_debt", "interest_arrears", "bondage_years_left")  # fields of the finance seat state


def holdings_in_use(holdings) -> bool:
	"""Whether the holdings hold anything: a field at its default, or a lazily made container with nothing in it, does not."""
	fresh = HoldingsState()
	for field in dataclasses.fields(holdings):
		value, default = getattr(holdings, field.name), getattr(fresh, field.name)
		if value == default or field.name == "_dashboard_history":
			continue
		if bool(value) or bool(default):
			return True
	return False


def stock_in_use(ledger_seat) -> bool:
	"""Whether the seat's tonnes ledger holds any tonnes: a lazily made ledger or snapshot with nothing in it does not."""
	stock, opening = ledger_seat._material_stock_ledger, ledger_seat._material_stock_opening
	return any((opening or {}).get("tonnes", {}).values()) or (any(stock.values()) if stock else False)


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
	if seat.modules["projects"].active or len(projects.business.entry_keys()):
		found.append("works")
	staff = seat.modules.get("workforce") or WorkforceSeat()
	if any(getattr(staff, name, 0) for name in STAFF_FIELDS) or staff.employees:
		found.append("staff")
	finance = seat.modules.get("finance") or FinanceSeat()
	if any(getattr(finance, name, 0) for name in OWED_FIELDS):
		found.append("arrears or bondage")
	if (holdings_in_use(seat.holdings) or stock_in_use(seat.modules.get("ledger") or LedgerSeat())
			or module_state_in_use(seat.modules.get("resources") or ResourcesSeat())
			or module_state_in_use(seat.modules.get("materials") or MaterialsSeat())):
		found.append("holdings")
	if (seat.modules.get("polity") or PolitySeat()).gov != 0.0:
		found.append("institutions")
	if seat.seat_progress != SeatProgressState():
		found.append("goal record")
	return found
