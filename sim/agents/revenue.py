"""A state's revenue: each form its civilisation declares, assessed on the base it names.

    revenue of a form = rate of the form * base the form is assessed on

A form is paid in coin, or in kind when it names the good (`paid_in`): a share of the harvest is taken as
grain, which goes to the state's stores and is used or sold through the goods market (government.py).
A form on land may be limited to the provinces it is levied in (`tiles`, or `except_tiles` of those held), so
one state can take a share of the crop in some and a share of assessed property in others.
"""
from dataclasses import dataclass
from typing import Any, FrozenSet, List, Optional, Tuple

from .revenue_bases import BASES, TILE_BASES


@dataclass(frozen=True)
class Assessment:
	form: str
	basis: str
	base: float  # money's worth of the base
	rate: float  # share of the base the state takes
	money: float  # money's worth of what it takes
	tonnes: float = 0.0  # what is taken in kind, in tonnes; zero for a form paid in coin
	material: str = ""  # the good taken in kind
	payers: Tuple[Tuple[Any, float], ...] = ()  # (actor, money) taken from actors, where the base is theirs

	@property
	def in_kind(self) -> bool:
		return bool(self.material)


def form_tiles(declared: Any, world: Any) -> Optional[FrozenSet[str]]:
	"""The tiles a form is levied on: those it lists, else those held, less any it excepts; None for a form
	on the whole state."""
	listed, excepted = declared.get("tiles"), declared.get("except_tiles")
	if listed is None and excepted is None:
		return None
	if declared["basis"] not in TILE_BASES:
		raise ValueError("form %r names tiles but its basis %r is national" % (declared["form"], declared["basis"]))
	chosen = set(listed) if listed is not None else set(world.held_tiles())
	return frozenset(chosen - set(excepted or ()))


def assess(world: Any) -> List[Assessment]:
	"""Every declared form assessed on this year's base, in the order the civilisation lists them."""
	assessments = []
	for declared in world.revenue_forms():
		tiles = form_tiles(declared, world)
		base = BASES[declared["basis"]](world) if tiles is None else BASES[declared["basis"]](world, tiles)
		rate = float(declared["rate"])
		material = declared.get("paid_in", "")
		if material and material != base.material:
			raise ValueError("form %r is paid in %r but its basis %r yields %r"
							 % (declared["form"], material, declared["basis"], base.material))
		if base.payers:
			assessments.append(taxed_actors(declared, base))
			continue
		assessments.append(Assessment(declared["form"], declared["basis"], base.value, rate, rate * base.value,
									  rate * base.tonnes if material else 0.0, material))
	return assessments


def taxed_actors(declared: Any, base: Any) -> Assessment:
	"""A form on what actors hold: each payer owes the rate of its own income, no more than its purse holds.
	A form may name the bodies it falls on (`from_strata`)."""
	rate = float(declared["rate"])
	names = declared.get("from_strata")
	chosen = [(payer, income) for payer, income in base.payers if names is None or payer.record.stratum in names]
	owed = tuple((payer, min(rate * income, max(0.0, payer.money))) for payer, income in chosen)
	return Assessment(declared["form"], declared["basis"], sum(income for _payer, income in chosen), rate,
					  sum(amount for _payer, amount in owed), payers=owed)
