"""The levers a player holding a country's government sets, and what the government reads of them.

Every lever is a field of the government's record (`levers`, plus the monopolies it already keeps), so a seat, another
player or an AI state pulls the same ones. `set_lever` is a plain function: it takes the record, a request and what the
country declares, and answers the change made or a `Refusal` with a `cause`; nothing is changed on a refusal. The
budget, revenue, works and surplus code read the record through the readers below; an unset lever leaves the
civilisation file's figure or the derived one in force.
"""
import math
from dataclasses import dataclass, field
from typing import Any, Collection, Dict, List, Union

from sim.refusal import Refusal

from . import state_works
from .budget_line import Line
from .revenue_bases import BASES
from .revenue_labour import BASIS as LABOUR_BASIS

REVENUE, BUDGET, ARMY, NAVY, WORKS, RESERVE, MONOPOLY, SUBSIDY, MANDATE = (
	"revenue", "budget", "army", "navy", "works", "reserve", "monopoly", "subsidy", "mandate")
LEVER_KINDS = (REVENUE, BUDGET, ARMY, NAVY, WORKS, RESERVE, MONOPOLY, SUBSIDY, MANDATE)
SCALAR_KINDS = (ARMY, NAVY, RESERVE)   # one figure, no name
DAYS_PER_YEAR = 365.0                  # the most days of labour a due can take

# the standing lines a budget lever can cut; each work's upkeep line is named for the work
BUDGET_LINES = ("army", "administration", "roads", "public_buildings", "court", "dole", "navy", "tax_collection",
				"campaign", "donative")

Change = Dict[str, Any]


@dataclass
class LeverContext:
	"""What the country declares and has: the forms its file lists, the goods it can name, and its people."""
	declared_forms: List[Dict[str, Any]] = field(default_factory=list)
	materials: Collection[str] = ()
	population: float = 0.0

	def revenue_names(self) -> List[str]:
		return [form["form"] for form in self.declared_forms]


def budget_line_names() -> List[str]:
	return list(BUDGET_LINES) + [work.name for work in state_works.WORKS]


def _refuse(cause: str, text: str, choices: Any = None, **facts: Any) -> Refusal:
	return Refusal(cause, text + " Nothing was changed.", choices, **facts)


def _number(value: Any, low: float, high: float, what: str) -> Union[float, Refusal]:
	if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
		return _refuse("value_not_number", "%s must be a number." % what, value=str(value))
	if not low <= value <= high:
		return _refuse("value_out_of_range", "%s must be between %g and %g, not %g." % (what, low, high, value),
					   low=low, high=high, value=value)
	return float(value)


def _store(levers: Dict[str, Any], kind: str, name: Any, value: Any) -> Any:
	"""Put `value` (None removes it) in the lever's slot; the value that was there."""
	if kind in SCALAR_KINDS:
		before = levers.get(kind)
		if value is None:
			levers.pop(kind, None)
		else:
			levers[kind] = value
		return before
	table = levers.setdefault(kind, {})
	before = table.get(name)
	if value is None:
		table.pop(name, None)
	else:
		table[name] = value
	if not table:
		levers.pop(kind, None)
	return before


def _set_revenue(record: Any, request: Dict[str, Any], context: LeverContext) -> Union[Change, Refusal]:
	name, rate_source = request.get("name"), request.get("value")
	declared = context.revenue_names()
	if rate_source is None:
		set_names = sorted(record.levers.get(REVENUE) or {})
		if name not in set_names:
			return _refuse("nothing_to_clear", "no rate has been set for %r." % (name,), set_names)
		before = _store(record.levers, REVENUE, name, None)
		return {"lever": REVENUE, "name": name, "before": before["rate"], "after": None}
	basis = request.get("basis")
	if name in declared:
		basis = next(form["basis"] for form in context.declared_forms if form["form"] == name)
	elif not isinstance(name, str) or not name.strip():
		return _refuse("unknown_name", "name the revenue form to set.", declared)
	elif basis is None:
		return _refuse("unknown_name", "%r is not a form of your state; name a basis to start one." % name, declared)
	elif basis not in BASES:
		return _refuse("unknown_basis", "%r is not a base the economy models." % (basis,), sorted(BASES))
	high = DAYS_PER_YEAR if basis == LABOUR_BASIS else 1.0
	rate = _number(rate_source, 0.0, high, "a rate")
	if isinstance(rate, Refusal):
		return rate
	slot = {"rate": rate}
	if name not in declared:
		slot["basis"] = basis
	before = _store(record.levers, REVENUE, name, slot)
	return {"lever": REVENUE, "name": name, "before": None if before is None else before["rate"], "after": rate,
			"basis": basis, "new_form": name not in declared}


def _set_monopoly(record: Any, request: Dict[str, Any], context: LeverContext) -> Union[Change, Refusal]:
	name, value = request.get("name"), request.get("value")
	if name not in context.materials:
		return _refuse("unknown_name", "%r is not a good the economy knows." % (name,), sorted(context.materials))
	if not isinstance(value, bool):
		return _refuse("value_not_boolean", "a monopoly is true (hold it) or false (release it).", [True, False], value=str(value))
	before = name in record.state_monopolies
	(record.state_monopolies.add if value else record.state_monopolies.discard)(name)
	return {"lever": MONOPOLY, "name": name, "before": before, "after": value}


def set_lever(record: Any, request: Dict[str, Any], context: LeverContext) -> Union[Change, Refusal]:
	"""Set (or, with a null `value`, clear) one lever of a government's record. `request` carries `lever` (a kind in
	`LEVER_KINDS`), `name` (the form, line, work or good, where the kind has several) and `value`. A change is
	`{lever, name, before, after}`; a refusal carries `cause` and `choices`."""
	kind = request.get("lever")
	if kind not in LEVER_KINDS:
		return _refuse("unknown_lever", "the levers are %s." % ", ".join(LEVER_KINDS), LEVER_KINDS, lever=str(kind))
	if kind == REVENUE:
		return _set_revenue(record, request, context)
	if kind == MONOPOLY:
		return _set_monopoly(record, request, context)
	name, value = request.get("name"), request.get("value")
	if kind not in SCALAR_KINDS:
		choices = {BUDGET: budget_line_names(), WORKS: [work.name for work in state_works.WORKS]}.get(kind, sorted(context.materials))
		if name not in choices:
			return _refuse("unknown_name", "%r is not a name for the %s lever." % (name, kind), choices, lever=kind)
	if value is not None:
		limits = {BUDGET: (0.0, 1.0, "a share of the line"), ARMY: (0.0, context.population, "an army"),
				  NAVY: (0.0, context.population, "a navy (ships)"), WORKS: (0.0, math.inf, "a stock of works (m2)"),
				  RESERVE: (0.0, math.inf, "a reserve (years of the standing need)"),
				  SUBSIDY: (0.0, math.inf, "a subsidy (money a year)"), MANDATE: (0.0, math.inf, "a mandate (tonnes a year)")}
		low, high, what = limits[kind]
		value = _number(value, low, high, what)
		if isinstance(value, Refusal):
			return value
	before = _store(record.levers, kind, name, value)
	return {"lever": kind, "name": None if kind in SCALAR_KINDS else name, "before": before, "after": value}


def current(record: Any) -> Dict[str, Any]:
	"""Every lever set on the record, with the monopolies it holds."""
	return dict(record.levers, **{MONOPOLY: sorted(record.state_monopolies)})


# ---- what the government reads ------------------------------------------------------------------------

def revenue_forms(declared: List[Dict[str, Any]], record: Any) -> List[Dict[str, Any]]:
	"""The declared forms at the rates the government has set, then the forms it has started."""
	overrides = record.levers.get(REVENUE) or {}
	forms = [dict(form, rate=overrides[form["form"]]["rate"]) if form["form"] in overrides else form for form in declared]
	known = {form["form"] for form in declared}
	return forms + [{"form": name, "basis": slot["basis"], "rate": slot["rate"]}
					for name, slot in sorted(overrides.items()) if name not in known]


def army_target(record: Any, derived: float) -> float:
	return float(record.levers.get(ARMY, derived))


def reserve_years(record: Any, derived: float) -> float:
	return float(record.levers.get(RESERVE, derived))


def scaled(record: Any, lines: List[Line]) -> List[Line]:
	"""The standing lines with each budget lever's share of its line kept."""
	shares = record.levers.get(BUDGET) or {}
	result = []
	for line in lines:
		share = shares.get(line.name, 1.0)
		result.append(line if share == 1.0 else Line(
			line.name, line.kind, {trade: people * share for trade, people in line.labour.items()}, line.wages * share,
			{commodity: tonnes * share for commodity, tonnes in line.materials.items()}, line.material_cost * share,
			line.transfer * share))
	return result


def lever_lines(record: Any, world: Any) -> List[Line]:
	"""A line for each subsidy (money handed to a good's producers) and mandate (tonnes of a good the state buys)."""
	lines = [Line("subsidy " + material, "requisition", transfer=amount)
			 for material, amount in sorted((record.levers.get(SUBSIDY) or {}).items()) if amount > 0.0]
	for material, tonnes in sorted((record.levers.get(MANDATE) or {}).items()):
		if tonnes > 0.0:
			lines.append(Line("mandate " + material, "requisition", {}, 0.0, {world.commodity_of(material): tonnes},
							  world.material_cost(material, tonnes)))
	return lines
