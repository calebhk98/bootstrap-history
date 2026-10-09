"""What a state's revenue forms are assessed on: bases the simulation models, each read from the world.

A civilisation's data names a basis for each form of revenue (`state_revenue` in its file). A basis is a
physical or monetary quantity of the modelled economy, never a share of a fitted total: the harvest, the
people able to work, the goods that crossed the border, the coin held. Adding a basis is one function
here and one line in `BASES`; no civilisation's id appears.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

# The grain the harvest is counted in, as a material in the tree's own terms.
HARVEST_MATERIAL = "wheat_kg"


@dataclass(frozen=True)
class Base:
	value: float  # money's worth of the base this year
	tonnes: float = 0.0  # physical amount where the base is a good, so a share of it can be paid in kind
	material: str = ""  # that good
	payers: Tuple[Tuple[Any, float], ...] = ()  # (actor, income) where the base is held by actors the state taxes


def harvest(world: Any) -> Base:
	tonnes = world.harvest_tonnes()
	return Base(tonnes * world.material_price(HARVEST_MATERIAL), tonnes, HARVEST_MATERIAL)


def adult_labour_years(world: Any) -> Base:
	"""The working age less the soldiers under arms (who owe no poll tax), each worth a year of unskilled
	labour at the going wage."""
	people = max(0.0, world.national_people("labourer") - world.soldiers_under_arms())
	return Base(people * world.pay_per_person_year("labourer"))


def imports_value(world: Any) -> Base:
	return Base(world.trade_value("in"))


def exports_value(world: Any) -> Base:
	return Base(world.trade_value("out"))


def coin_stock(world: Any) -> Base:
	"""Coin the society holds: the only wealth the simulation models as a stock."""
	return Base(world.coin_stock_value())


def earned_income(stratum: Any) -> float:
	"""What a body of people has earned from outside the modelled actors over its life (wages, property,
	harvest): what flows between actors (migration, keep, relief) is not earned."""
	return sum(amount for purpose, amount in stratum.record.income.items() if purpose.startswith("edge:"))


def stratum_income(world: Any) -> Base:
	"""What each of the country's bodies of people earned since the state last assessed it; the money is
	taken from the bodies themselves (`ledger.transfer`), so the payers go with the base."""
	assessed = world.government().record.income_assessed
	payers = tuple((stratum, max(0.0, earned_income(stratum) - assessed.get(stratum.actor_id, 0.0)))
				   for stratum in world.country_strata())
	return Base(sum(income for _stratum, income in payers), payers=payers)


def land_rent(world: Any) -> Base:
	"""Rent producers paid on the land they let last year, summed over the tiles; the owners who received it
	are the payers where the world can name them."""
	owners = tuple(world.land_rent_owners())
	return Base(sum(world.land_rent_paid_by_tile().values()), payers=owners)


def land_value(world: Any) -> Base:
	"""What the land let is worth: the rent capitalised at the market rate of interest, so land is worth what
	its rent would buy in the loan market. Nothing is taxable where there is no rate."""
	rate = world.market_rate()
	base = land_rent(world)
	if rate <= 0.0:
		return Base(0.0)
	return Base(base.value / rate, payers=tuple((owner, rent / rate) for owner, rent in base.payers))


BASES: Dict[str, Callable[[Any], Base]] = {
	"harvest": harvest,
	"adult_labour_years": adult_labour_years,
	"imports_value": imports_value,
	"exports_value": exports_value,
	"coin_stock": coin_stock,
	"stratum_income": stratum_income,
	"land_rent": land_rent,
	"land_value": land_value,
}
