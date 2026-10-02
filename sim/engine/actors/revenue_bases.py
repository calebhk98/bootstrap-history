"""What a state's revenue forms are assessed on: bases the simulation models, each read from the world.

A civilisation's data names a basis for each form of revenue (`state_revenue` in its file). A basis is a
physical or monetary quantity of the modelled economy, never a share of a fitted total: the harvest, the
people able to work, the goods that crossed the border, the coin held. Adding a basis is one function
here and one line in `BASES`; no civilisation's id appears.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict

# The grain the harvest is counted in, as a material in the tree's own terms.
HARVEST_MATERIAL = "wheat_kg"


@dataclass(frozen=True)
class Base:
	value: float  # money's worth of the base this year
	tonnes: float = 0.0  # physical amount where the base is a good, so a share of it can be paid in kind
	material: str = ""  # that good


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


BASES: Dict[str, Callable[[Any], Base]] = {
	"harvest": harvest,
	"adult_labour_years": adult_labour_years,
	"imports_value": imports_value,
	"exports_value": exports_value,
	"coin_stock": coin_stock,
}
