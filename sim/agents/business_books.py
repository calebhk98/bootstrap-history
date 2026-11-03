"""A business's yearly books: what a plant takes, costs and pays, the same arithmetic for any owner."""
from typing import Any, Optional, Tuple

from . import adoption, firm_entry, ledger
from .business import Business
from .business_crew import staff
from .edges import EDGE_CUSTOMERS, EDGE_LANDOWNERS, EDGE_SUPPLIERS


def takings_of_size(takings_of_one_unit: float, size: float, market_factor: float) -> float:
	"""A plant's takings at `size` founding units: its figure for one unit at its ramp, times its size, times the
	price the goods market gives its goods. The one product the founder's quote and a firm's books both use."""
	return takings_of_one_unit * size * market_factor


def operate(business: Business, owner: Any, entry_key: str, world: Any, rivals: float) -> float:
	"""One year of a plant: staff it, take its takings, pay upkeep, wages, levy and royalty.
	Returns the year's margin."""
	weight = adoption.plant_weight(owner.adoption, entry_key)   # the share of the plant that runs the technique
	size = business.reading.size_of(entry_key) * weight
	books = world.enterprises.plant_books(entry_key, business.reading.opened_year_of(entry_key, world.setting.year), rivals, size)
	if books is None:   # the plant's country keeps no record of a figure its books need: it stands idle
		business.tally.note_crew_found(entry_key, 0.0)
		business.tally.note_takings(entry_key, 0.0)
		return 0.0
	found = staff(business, owner, entry_key, world, weight)
	business.tally.note_crew_found(entry_key, found)
	takings = found * books.takings
	business.tally.note_takings(entry_key, takings)
	upkeep = books.upkeep
	wages = found * books.wages   # at the economy's wage for each trade (the core's clearing pays the crew, not here)
	if not world.market.sells_on_book(entry_key):   # what sells in the book is paid when the year's market clears
		ledger.transfer(world.setting.edge(EDGE_CUSTOMERS), owner, takings, "takings")
	ledger.pay_up_to(owner, world.setting.edge(EDGE_SUPPLIERS), upkeep, "upkeep")   # the margin carries the whole upkeep; what the owner cannot pay stays unpaid
	state = world.setting.government()
	levy = 0.0 if state is owner else state.collect(owner, takings, world)   # a state does not levy its own works
	royalty = world.disclosure.collect_royalty(owner, entry_key, takings)
	return takings - upkeep - wages - levy - royalty


def carry(business: Business, owner: Any, entry_key: str, world: Any) -> Optional[float]:
	"""Pay the rent on the land a plant occupies whatever it sells, and post its managers' places to the labour market
	(hired and paid by the clearing like any crew; the same costs an entrant weighs, firm_entry.carrying_cost).
	Returns the rent paid plus the managers' estimated pay; None when the plant's country gives no reading of the rent
	(nothing is paid or posted, and the caller decides what a margin without it means)."""
	size = business.reading.size_of(entry_key)
	rent = world.site.site_rent(entry_key, size, owner.location())
	if rent is None:   # the plant's country keeps no record of the rent: it pays nothing it cannot read
		return None
	trade, people = firm_entry.management_places(world, entry_key, size)
	ledger.pay_up_to(owner, world.setting.edge(EDGE_LANDOWNERS), rent, "site rent")   # the rent counts in full; an owner short of it pays what it can
	if trade is None:
		return rent
	posted = owner.record.staff_wanted
	posted[trade] = posted.get(trade, 0.0) + people
	return rent + people * world.labour.hours_per_person_year * world.labour.hourly_pay(trade)


def yearly_costs(world: Any, entry_key: str) -> Optional[Tuple[float, float]]:
	"""(upkeep, wage bill) of a plant of the entry at its founding size: what a new operator expects to pay; None
	when the actor's country keeps no record of a figure they need."""
	return world.concerns.plant_costs(entry_key)


def ramp(business: Business, entry_key: str, world: Any) -> float:
	"""How far a plant has ramped up, 0..1."""
	return world.concerns.ramp(business.reading.opened_year_of(entry_key, world.setting.year), entry_key)


def any_ramping(business: Business, world: Any) -> bool:
	"""Whether any plant is still ramping up: the industry's depth sets how long that takes."""
	return any(ramp(business, entry_key, world) < 1.0 for entry_key in business.reading.entry_keys())
