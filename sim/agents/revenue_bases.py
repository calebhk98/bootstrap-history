"""What a state's revenue forms are assessed on: bases the simulation models, each read from the world.

A civilisation's data names a basis for each form of revenue (`state_revenue` in its file). A basis is a
physical or monetary quantity of the modelled economy, never a share of a fitted total: the harvest, the
people able to work, the goods that crossed the border, the coin held. Adding a basis is one function
here and one line in `BASES`; no civilisation's id appears.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, Optional, Tuple


@dataclass(frozen=True)
class Base:
	value: float  # money's worth of the base this year
	tonnes: float = 0.0  # physical amount where the base is a good, so a share of it can be paid in kind
	material: str = ""  # that good
	payers: Tuple[Tuple[Any, float], ...] = ()  # (actor, income) where the base is held by actors the state taxes


def harvest(world: Any, tiles: Optional[FrozenSet[str]] = None, material: Optional[str] = None) -> Base:
	"""What the land yielded of the good a form is paid in. Grain is the farm's harvest (on named tiles, their
	share of it: TEMPORARY HEURISTIC (CLAUDE.md 4.4), spread over the state's tiles by arable hectares, as no
	harvest is recorded by tile, retire: Complaint 622); any other good is what the country's producers made of
	it last year, tile by tile."""
	staple = world.quotes.staple_material()   # the grain the harvest is counted in: the civilisation's staple
	if material is not None and material != staple:
		tonnes = world.revenue.output_tonnes(material, tiles)
		return Base(tonnes * world.quotes.material_price(material), tonnes, material)
	tonnes = world.revenue.harvest_tonnes() * (1.0 if tiles is None else world.revenue.arable_share(tiles))
	return Base(tonnes * world.quotes.material_price(staple), tonnes, staple)


def adult_labour_years(world: Any) -> Base:
	"""The working age less the soldiers under arms (who owe no poll tax), each worth a year of unskilled
	labour at the going wage."""
	people = max(0.0, world.labour.national_people(world.labour.trade_of_role("unskilled")) - world.army.soldiers_under_arms())
	return Base(people * world.labour.pay_per_person_year(world.labour.trade_of_role("unskilled")))


def imports_value(world: Any) -> Base:
	return Base(world.revenue.trade_value("in"))


def exports_value(world: Any) -> Base:
	return Base(world.revenue.trade_value("out"))


def coin_stock(world: Any) -> Optional[Base]:
	"""Coin the society holds: the only wealth the simulation models as a stock. None when the coin metal has no price, so the
	form is not assessed."""
	value = world.revenue.coin_stock_value()
	return None if value is None else Base(value)


def earned_income(stratum: Any) -> float:
	"""What a body of people has earned from outside the modelled actors over its life (wages, property,
	harvest): what flows between actors (migration, keep, relief) is not earned."""
	return sum(amount for purpose, amount in stratum.record.income.items() if purpose.startswith("edge:"))


def stratum_income(world: Any) -> Base:
	"""What each of the country's bodies of people earned since the state last assessed it; the money is
	taken from the bodies themselves (`ledger.transfer`), so the payers go with the base."""
	assessed = world.setting.government().record.income_assessed
	payers = tuple((stratum, max(0.0, earned_income(stratum) - assessed.get(stratum.actor_id, 0.0)))
				   for stratum in world.people.country_strata())
	return Base(sum(income for _stratum, income in payers), payers=payers)


def land_rent(world: Any, tiles: Optional[FrozenSet[str]] = None) -> Base:
	"""Rent producers paid on the land they let last year, summed over the tiles (only `tiles` when given); the
	owners who received it are the payers where the world can name them."""
	paid = world.revenue.land_rent_paid_by_tile()
	total = sum(rent for tile, rent in paid.items() if tiles is None or tile in tiles)
	return Base(total, payers=tuple(world.revenue.land_rent_owners(tiles)) if total > 0.0 else ())


def land_value(world: Any, tiles: Optional[FrozenSet[str]] = None) -> Base:
	"""What the land let is worth: the rent capitalised at the market rate of interest, so land is worth what
	its rent would buy in the loan market. Nothing is taxable where there is no rate."""
	rate = world.credit.market_rate()
	base = land_rent(world, tiles)
	if rate <= 0.0:
		return Base(0.0)
	return Base(base.value / rate, payers=tuple((owner, rent / rate) for owner, rent in base.payers))


BASES: Dict[str, Callable[[Any], Optional[Base]]] = {
	"harvest": harvest,
	"adult_labour_years": adult_labour_years,
	"imports_value": imports_value,
	"exports_value": exports_value,
	"coin_stock": coin_stock,
	"stratum_income": stratum_income,
	"land_rent": land_rent,
	"land_value": land_value,
}

# The bases that can be limited to named tiles (a form's `tiles` / `except_tiles`); the rest are national.
TILE_BASES = frozenset({"harvest", "land_rent", "land_value"})

# The bases that read the good a form is paid in (`paid_in`), so one basis serves every good.
GOOD_BASES = frozenset({"harvest"})
