"""The one rule for a plant's crew: who a plant of an entry ties up, whoever owns it.

Plain functions over `CrewFigures`, the plant's own data read once by the caller. The founder's screens and gates
and a firm's staffing both get their people from here; nothing outside `sim/agents/business*.py` and the plant
kernel computes a crew."""
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Tuple

from sim.world import plant_figures

# Trades that are generic labour: a foreman is never drawn from them.
GENERIC_TRADES = ("artisan", "labourer", "slave")


@dataclass(frozen=True)
class CrewFigures:
	"""What the crew rule reads about one plant. Heuristic knobs (supervision share, hands per revenue, foreman
	share) come from the caller, which declares them."""
	scholars_figure: float
	artisans_figure: float
	revenue: float
	upkeep: float
	hours_per_person_year: float
	supervision_share: float
	hands_per_revenue: Callable[[], float]   # asked only when the plant's revenue sets its crew
	foreman_share: float
	unskilled_trade: Callable[[], str]   # asked only when a plant states no hours
	is_capability_institution: bool = False
	stated_people: Optional[float] = None
	revenue_basis: Optional[str] = None
	hours_by_trade: Optional[Mapping[str, float]] = None
	build_hours_by_trade: Mapping[str, float] = field(default_factory=dict)
	garrison: Mapping[str, float] = field(default_factory=dict)


def figures_of(node: Mapping, unskilled_trade: Callable[[], str], hours_per_person_year: float, supervision_share: float,
			   hands_per_revenue: Callable[[], float], foreman_share: float, is_capability_institution: bool,
			   garrison: Mapping[str, float]) -> CrewFigures:
	"""A plant's crew figures from its tree node (the one place the node's money fields are read for a crew)."""
	return CrewFigures(
		scholars_figure=node.get("sch", 0.0), artisans_figure=node.get("art", 0.0), revenue=node.get("rev", 0.0),
		upkeep=node.get("up", 0.0), hours_per_person_year=hours_per_person_year, supervision_share=supervision_share,
		hands_per_revenue=hands_per_revenue, foreman_share=foreman_share, unskilled_trade=unskilled_trade,
		is_capability_institution=is_capability_institution, stated_people=node.get("plant_crew_people"),
		revenue_basis=node.get("_revenue_basis"), hours_by_trade=node.get("_labour_hours_per_year"),
		build_hours_by_trade=node.get("lab") or {}, garrison=garrison)


def founder_staffed_hands(figures: CrewFigures) -> Tuple[float, float]:
	"""(scholars, craftsmen) a plant needs while its founder still runs it."""
	# Capability institutions (school, workshop) and net-loss concerns tie up no supervision staff.
	if figures.is_capability_institution and figures.revenue <= figures.upkeep:
		return 0.0, 0.0
	by_size = max(0.0, figures.revenue) / figures.hands_per_revenue()
	derived_hours = plant_figures.derived_crew_hours(figures.revenue_basis, figures.hours_by_trade)
	# the plant's own crew where its data states one; the takings-based rule is only the fallback
	crew = plant_figures.crew_people(derived_hours, figures.hours_per_person_year, figures.stated_people,
									 max(figures.artisans_figure * figures.supervision_share, by_size))
	return figures.scholars_figure * figures.supervision_share, crew


def hands(figures: CrewFigures, runs_without_founder: Callable[[], bool]) -> Tuple[float, float]:
	"""(scholars, craftsmen) a plant ties up: once the staff hold a year's running of the technique, the plant
	runs without its founder and the scholars drop out. `runs_without_founder` is asked only when scholars are held."""
	scholars, craftsmen = founder_staffed_hands(figures)
	if scholars > 0.0 and runs_without_founder():
		return 0.0, craftsmen
	return scholars, craftsmen


def crew_by_trade(figures: CrewFigures) -> Dict[str, float]:
	"""{trade: people} the plant keeps busy: the trades its lines name; a plant whose data states no hours has its
	fallback crew from the unskilled trade."""
	craftsmen = founder_staffed_hands(figures)[1]
	if craftsmen > 0.0 and plant_figures.derived_crew_hours(figures.revenue_basis, figures.hours_by_trade) > 0.0:
		return plant_figures.crew_by_trade(figures.hours_by_trade or {}, figures.hours_per_person_year)
	return {figures.unskilled_trade(): craftsmen} if craftsmen > 0.0 else {}


def foreman(figures: CrewFigures) -> Tuple[Optional[str], float]:
	"""(skilled trade, FTE) that supervises the plant, or (None, 0): the largest skilled share of its build crew.
	A plant built by generic artisans alone, or a capability institution, has none."""
	if (figures.is_capability_institution or figures.revenue <= 0
			or figures.build_hours_by_trade.get("artisan", 0) <= 0):
		return None, 0.0
	skilled = [(hours, trade) for trade, hours in figures.build_hours_by_trade.items()
			   if trade not in GENERIC_TRADES and hours > 0]
	if not skilled:
		return None, 0.0
	_hours, trade = max(skilled, key=lambda row: (row[0], row[1]))
	return trade, figures.foreman_share


def staff_by_trade(figures: CrewFigures, scholars: float) -> Dict[str, float]:
	"""{trade: people} one plant needs of the shared pool: its crew, the scholars it ties up, its foreman and its
	garrison. `scholars` is `hands(...)[0]`."""
	staff = dict(crew_by_trade(figures))
	staff["scholar"] = scholars
	foreman_trade, foreman_fte = foreman(figures)
	if foreman_trade:
		staff[foreman_trade] = staff.get(foreman_trade, 0.0) + foreman_fte
	for trade, people in figures.garrison.items():
		staff[trade] = staff.get(trade, 0.0) + people
	return {trade: people for trade, people in staff.items() if people > 0.0}
