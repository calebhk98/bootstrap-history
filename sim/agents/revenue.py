"""A state's revenue: each form its civilisation declares, assessed on the base it names.

    revenue of a form = rate of the form * base the form is assessed on

A form is paid in coin, or in kind when it names the good (`paid_in`): a share of what the land yielded of that
good (grain, wine, oil, cloth, livestock: any good the country's producers make) is taken, which goes to the state's stores and is used or sold through the goods market (government.py).
A form on land may be limited to the provinces it is levied in (`tiles`, or `except_tiles` of those held), so
one state can take a share of the crop in some and a share of assessed property in others.
"""
from dataclasses import dataclass, replace
from typing import Any, FrozenSet, List, Optional, Tuple

from . import authority, evasion, revenue_labour
from .revenue_bases import BASES, GOOD_BASES, TILE_BASES


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
	person_days: float = 0.0  # labour owed, in days of work, where the form is a labour due (revenue_labour.py)
	labour_to: str = ""  # what the labour is for: the state's works or its army
	commute: float = 0.0  # the share of a labour due paid in coin instead
	collectible: float = 1.0  # share of what is due that the state's officials reach (collection.py); money and tonnes are after it
	concealed: float = 0.0  # money's worth of the payers' income kept off the rolls (evasion.py); `base` is what remains
	kept_by_officials: float = 0.0  # share of what was collected that officials kept (authority.py); money and tonnes are after it

	@property
	def in_kind(self) -> bool:
		return bool(self.material)

	@property
	def in_labour(self) -> bool:
		return bool(self.labour_to)

	@property
	def hours(self) -> float:
		"""Hours of work owed, before any commuted to coin."""
		return self.person_days * revenue_labour.HOURS_PER_WORKING_DAY

	@property
	def coin_money(self) -> float:
		"""Money that reaches the purse from nowhere the actors' books show: not goods, and of a labour due only
		the commuted share."""
		if self.in_kind or self.payers:
			return 0.0
		return self.commute * self.money if self.in_labour else self.money


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
		if declared["basis"] == revenue_labour.BASIS:
			assessments.append(labour_due(declared, world))
			continue
		tiles = form_tiles(declared, world)
		material = declared.get("paid_in", "")
		measure = BASES[declared["basis"]]
		if declared["basis"] in GOOD_BASES and material:
			base = measure(world, tiles, material)
		else:
			base = measure(world) if tiles is None else measure(world, tiles)
		rate = float(declared["rate"])
		if material and material != base.material:
			raise ValueError("form %r is paid in %r but its basis %r yields %r"
							 % (declared["form"], material, declared["basis"], base.material))
		collectible = world.collectible_share(tiles)
		kept = authority.kept_on(world, tiles)
		if base.payers:
			assessments.append(leaked(taxed_actors(declared, base, collectible), kept))
			continue
		assessments.append(leaked(Assessment(declared["form"], declared["basis"], base.value, rate, collectible * rate * base.value,
											 collectible * rate * base.tonnes if material else 0.0, material,
											 collectible=collectible), kept))
	return assessments


def leaked(assessment: Assessment, kept: float) -> Assessment:
	"""The assessment after officials have kept their share of what they collected (the share is not booked as revenue)."""
	if kept <= 0.0:
		return assessment
	return replace(assessment, money=authority.after_leakage(assessment.money, kept),
				   tonnes=authority.after_leakage(assessment.tonnes, kept),
				   payers=tuple((payer, authority.after_leakage(owed, kept)) for payer, owed in assessment.payers),
				   kept_by_officials=kept)


def taxed_actors(declared: Any, base: Any, collectible: float = 1.0) -> Assessment:
	"""A form on what actors hold: each payer keeps part of its income off the rolls (evasion.py, by the rate and the
	state's reach) and owes the rate of the rest, no more than its purse holds, and the state reaches the
	`collectible` share of it. A form may name the bodies it falls on (`from_strata`)."""
	rate = float(declared["rate"])
	names = declared.get("from_strata")
	chosen = [(payer, income) for payer, income in base.payers if names is None or payer.record.stratum in names]
	declared_by_payer = [(payer, evasion.declared_income(income, rate, collectible)) for payer, income in chosen]
	owed = tuple((payer, collectible * min(rate * seen, max(0.0, payer.money))) for payer, seen in declared_by_payer)
	gross = sum(income for _payer, income in chosen)
	seen_total = sum(seen for _payer, seen in declared_by_payer)
	return Assessment(declared["form"], declared["basis"], seen_total, rate, sum(amount for _payer, amount in owed),
					  payers=owed, collectible=collectible, concealed=gross - seen_total)


def labour_due(declared: Any, world: Any) -> Assessment:
	"""Labour owed: the base is a year of the liable people's work at the going wage, the rate the share of a working
	year the days come to, so the money's worth is what the state would pay for the labour."""
	levy = revenue_labour.levy_of(declared, world)
	share_of_year = (float(declared["rate"]) * revenue_labour.HOURS_PER_WORKING_DAY) / world.hours_per_person_year
	base = levy.people * world.pay_per_person_year("labourer")
	return Assessment(declared["form"], declared["basis"], base, share_of_year, share_of_year * base,
					  person_days=levy.person_days, labour_to=levy.destination, commute=levy.commute)
