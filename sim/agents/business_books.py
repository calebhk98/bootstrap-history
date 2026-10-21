"""A business's yearly books: what a plant takes, costs and pays, the same arithmetic for any owner."""
from typing import Any, Tuple

from . import firm_entry, ledger
from .business import Business
from .business_crew import staff
from .edges import EDGE_CUSTOMERS, EDGE_LANDOWNERS, EDGE_SUPPLIERS, EDGE_WORKERS


def takings_of_size(takings_of_one_unit: float, size: float, market_factor: float) -> float:
	"""A plant's takings at `size` founding units: its figure for one unit at its ramp, times its size, times the
	price the goods market gives its goods. The one product the founder's quote and a firm's books both use."""
	return takings_of_one_unit * size * market_factor


def operate(business: Business, owner: Any, entry_key: str, world: Any, rivals: float) -> float:
	"""One year of a plant: staff it, take its takings, pay upkeep, wages, levy and royalty.
	Returns the year's margin."""
	size = business.size_of(entry_key)
	books = world.plant_books(entry_key, business.opened_year_of(entry_key, world.year), rivals, size)
	if books is None:   # the plant's country keeps no record of a figure its books need: it stands idle
		business.note_crew_found(entry_key, 0.0)
		business.note_takings(entry_key, 0.0)
		return 0.0
	found = staff(business, owner, entry_key, world)
	business.note_crew_found(entry_key, found)
	takings = found * books.takings
	business.note_takings(entry_key, takings)
	upkeep = books.upkeep
	wages = found * books.wages
	if not world.sells_on_book(entry_key):   # what sells in the book is paid when the year's market clears
		ledger.transfer(world.edge(EDGE_CUSTOMERS), owner, takings, "takings")
	ledger.transfer(owner, world.edge(EDGE_SUPPLIERS), upkeep, "upkeep")
	if owner.record.country is None:
		world.pay_wages(owner, wages, "wages")
	else:
		ledger.transfer(owner, world.edge(EDGE_WORKERS), wages, "wages")
	state = world.government()
	levy = 0.0 if state is owner else state.collect(owner, takings, world)   # a state does not levy its own works
	royalty = world.collect_royalty(owner, entry_key, takings)
	return takings - upkeep - wages - levy - royalty


def carry(business: Business, owner: Any, entry_key: str, world: Any) -> float:
	"""Pay what running a plant costs whatever it sells: rent on the land it occupies and a manager's hours
	(the same costs an entrant weighs, firm_entry.carrying_cost). Returns the sum paid."""
	size = business.size_of(entry_key)
	rent = world.site_rent(entry_key, size, owner.location())
	management = firm_entry.management_cost(world, entry_key, size)
	ledger.transfer(owner, world.edge(EDGE_LANDOWNERS), rent, "site rent")
	if owner.record.country is None:
		world.pay_wages(owner, management, "management")
	else:
		ledger.transfer(owner, world.edge(EDGE_WORKERS), management, "management")
	return rent + management


def yearly_costs(world: Any, entry_key: str) -> Tuple[float, float]:
	"""(upkeep, wage bill) of a plant of the entry at its founding size: what a new operator expects to pay."""
	return world.upkeep(entry_key), world.concern_wage_bill(entry_key)


def ramp(business: Business, entry_key: str, world: Any) -> float:
	"""How far a plant has ramped up, 0..1."""
	return world.ramp(business.opened_year_of(entry_key, world.year), entry_key)


def any_ramping(business: Business, world: Any) -> bool:
	"""Whether any plant is still ramping up: the industry's depth sets how long that takes."""
	return any(ramp(business, entry_key, world) < 1.0 for entry_key in business.entry_keys())
