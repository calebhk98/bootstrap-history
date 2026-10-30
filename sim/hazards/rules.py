"""Hazards' rules: plain functions of plain values. The module's methods fetch the inputs from views and send the results."""
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .constants import HAZARD_KINDS, HAZARD_TIMELINE_BEGIN_NOW_MULT


# ---- what built defences take off a harm ----

def counter_strength(held: bool, running: bool, residue: float) -> float:
	"""Fraction of a counter's relief in force: none if never built, full while it is knowledge or a running concern, a
	residue once a concern has been closed."""
	if not held:
		return 0.0
	return 1.0 if running else residue


def counter_requirements(node: Dict[str, Any], kind: str, label: str) -> Sequence[str]:
	"""Node ids a counter needs running as well (`requires_running` on its `hazard_counters` entry)."""
	for counter in (node.get("mechanics") or {}).get("hazard_counters", ()):
		if counter["kind"] == kind and counter["label"] == label:
			return counter.get("requires_running") or ()
	return ()


def own_mine_strength(capacity: float, floor: float) -> float:
	"""A counter that is the seat's own mine: full while the mine yields more than `floor`."""
	return 1.0 if capacity > floor else 0.0


def relief_product(entries: Iterable[Dict[str, Any]]) -> float:
	"""Each counter removes a share of what is left, so the factors multiply."""
	multiplier = 1.0
	for entry in entries:
		multiplier *= entry["factor"]
	return multiplier


def removed_shares(entries: List[Dict[str, Any]]) -> List[float]:
	"""For each defence, the share of the unmitigated harm it removes given all the others."""
	total = relief_product(entries)
	removed = []
	for index in range(len(entries)):
		others = 1.0
		for other_index, other in enumerate(entries):
			if other_index != index:
				others *= other["factor"]
		removed.append(others - total)
	return removed


def output_floor(hazard_factor: float, relief: float) -> float:
	"""The lowest the output factor falls in a hazard year; relief moves the floor back toward 1.0."""
	return 1.0 - (1.0 - hazard_factor) * relief


def staff_exposure(historical: float, national_relief: float, relief: float) -> Dict[str, float]:
	"""The staff a household loses to one wave: the country's public health lowers the rate first, the household's own
	defences then count where the nation has not adopted them."""
	before_defences = historical * (1.0 - national_relief)
	return {"national_relief": national_relief, "before_defences": before_defences, "relief": relief,
		"loss": before_defences * relief}


def hazard_kinds_in(hazard: Dict[str, Any]) -> List[str]:
	return [kind for kind in HAZARD_KINDS if kind in hazard]


def counters_by_kind(rows: Dict[str, List[Tuple[Any, ...]]], own_sources: Dict[str, List[Tuple[Any, ...]]]) -> Dict[str, list]:
	"""{kind: [(node or pseudo-source, share, label)]}: the node rows with the counters that are not nodes merged in, each
	kind ordered by its whole row."""
	merged = {kind: list(own) for kind, own in own_sources.items()}
	for kind, found in rows.items():
		merged.setdefault(kind, []).extend(found)
	return {kind: [(node, share, label) for _order, node, share, label in sorted(entries)]
		for kind, entries in merged.items()}


def war_relief(leverage: float, relief_cap: float) -> Tuple[float, Optional[str]]:
	"""(multiplier on a war's output harm, reason) at a military leverage; nothing to say at none."""
	if leverage <= 0.0:
		return 1.0, None
	share = relief_cap * leverage
	return (1.0 - share), ("an army and treasury the state can call on (military strength %d%%)" % round(leverage * 100))


def entry_words(entry: Dict[str, Any], lapsed_name: Optional[str], closure_words: Optional[str]) -> str:
	"""A defence's label with what has lapsed or is partly adopted nationally."""
	label = entry["label"]
	if entry.get("short_of"):
		label = "%s (lapsed: %s)" % (label, entry["short_of"])
	if entry.get("lapsed_node"):
		label = "%s (lapsed: %s is closed %s)" % (label, lapsed_name, closure_words)
	if entry.get("partly_adopted_nationally"):
		label = "%s (partly adopted nationally)" % label
	return label


def closure_words(record: Optional[Dict[str, Any]], reason_words: Dict[str, str]) -> str:
	"""Why a concern is shut, in words."""
	if record is None:
		return "and has not been opened"
	return reason_words.get(record["reason"], "")


# ---- the corpus: what a sack can take ----

def losable_after_roll(losable: List[str], fraction: float) -> int:
	"""How many of the losable technologies a sack that takes any takes (at least one)."""
	return max(1, int(len(losable) * fraction))


def corpus_loss_message(forgotten: List[str], hedge_was_best: bool, corpus_lost: List[str], on_road: int) -> str:
	"""What a sack's corpus loss took, and what it does to the goal road."""
	named = sorted(forgotten)
	return ("KNOWLEDGE LOST: %d technolog%s forgotten - %s%s%s%s"
		% (len(forgotten), "y" if len(forgotten) == 1 else "ies",
		   ", ".join(named[:8]) + (" and %d more" % (len(named) - 8) if len(named) > 8 else ""),
		   "" if hedge_was_best else " (the corpus was never printed and dispersed)",
		   ". THE CORPUS ITSELF WENT (%s): your hedge against this is gone and 'risk' will say so "
		   "- build it again first" % ", ".join(corpus_lost) if corpus_lost else "",
		   (". %d of these stood on the road to your goal: the route is longer than it was a "
		    "moment ago - 'path' will show the rebuilt shape of it" % on_road) if on_road else ""))


# ---- the output factor ----

def recovered_output_factor(factor: float, base_rate: float, leverage: float) -> float:
	"""The output factor after a year's recovery: the base rate, doubled at full military leverage, never above 1."""
	return min(1.0, factor + base_rate * (1.0 + leverage))


def lowered_output_factor(current: float, floors: Iterable[float]) -> float:
	"""The world takes the highest floor any seat's works leave, and the factor never rises in a hazard."""
	return min(current, max(floors))


# ---- the hazards ahead: timeline and wording ----

def years_words(years: float) -> str:
	years = round(years)
	return "%d year" % years if years == 1 else "%d years" % years


def timeline_state(in_progress: bool, worst_multiplier: float, years_until: float, quick_hedge: Optional[float],
		strong_hedge: Optional[float], name: str) -> Tuple[str, str]:
	"""(urgency, headline) for one hazard: years until it lands against the lead time of the hedges."""
	hedged = worst_multiplier <= 0.75
	years_text = years_words(years_until)
	if in_progress:
		return "happening now", ("%s: under way now%s" % (name, "" if hedged else ", and built defences do not cover most of it"))
	if hedged:
		return "hedged", "%s: %s off, already well hedged" % (name, years_text)
	if quick_hedge is None:
		return "no hedge found", "%s: %s off, unhedged, no hedge visible yet" % (name, years_text)
	if years_until <= quick_hedge:
		return "too late to hedge", ("%s: only %s left; even the fastest hedge needs about %s - it is coming regardless"
			% (name, years_text, years_words(quick_hedge)))
	if strong_hedge and strong_hedge > quick_hedge and years_until <= strong_hedge:
		return "stopgap only", ("%s: %s off - a quick hedge (%s) could still finish, the strong one (%s) could not"
			% (name, years_text, years_words(quick_hedge), years_words(strong_hedge)))
	if years_until <= (strong_hedge or quick_hedge) * HAZARD_TIMELINE_BEGIN_NOW_MULT:
		return "begin hedge now", ("%s: %s off; the real hedge needs %s - time is short"
			% (name, years_text, years_words(strong_hedge or quick_hedge)))
	return "on the horizon", ("%s: %s off, unhedged, plenty of time to build one (%s)"
		% (name, years_text, years_words(strong_hedge or quick_hedge)))


def hedge_lead_times(advice: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
	"""(quickest, slowest) calendar floor of the hedges in a piece of advice, or (None, None)."""
	floor = advice.get("even_started_today_the_real_hedges_here_take_years")
	if isinstance(floor, dict):
		return floor.get("quickest"), floor.get("slowest")
	if isinstance(floor, (int, float)):
		return floor, floor
	return None, None


def compact_timeline(rows: List[Dict[str, Any]], warn_tags: Iterable[str]) -> List[Dict[str, Any]]:
	"""The nearest row keeps its sentence; a later one only if it is a warning."""
	for index, row in enumerate(rows):
		if index == 0 or row["urgency"] in warn_tags:
			continue
		row.pop("headline", None)
		row.pop("in_progress", None)
	return rows


# ---- the world event log ----

def world_event_entry(year: int, kind: str, actors: Iterable[Any], tiles: Iterable[Any], cause: str, facts: Dict[str, Any]) -> Dict[str, Any]:
	return {"year": int(year), "kind": kind, "actors": [str(actor) for actor in actors],
		"tiles": [str(tile) for tile in tiles], "cause": cause, "facts": dict(facts)}


def trim_world_events(kept: List[Dict[str, Any]], years_kept: int) -> None:
	"""Drop, in place, the records older than `years_kept` years before the newest."""
	oldest = kept[-1]["year"] - years_kept
	if kept[0]["year"] <= oldest:
		kept[:] = [row for row in kept if row["year"] > oldest]


def world_event_rows(events: Iterable[Dict[str, Any]], kind: Optional[str] = None, since_year: Optional[int] = None,
		actor: Optional[str] = None) -> List[Dict[str, Any]]:
	"""The records, oldest first, optionally of one kind, from a year on, or involving one actor."""
	return [dict(row) for row in events
		if (kind is None or row["kind"] == kind)
		and (since_year is None or row["year"] >= since_year)
		and (actor is None or actor in row["actors"])]


def famine_shortfall(strata: Iterable[Tuple[float, float]]) -> Tuple[float, float]:
	"""(people, their food shortfall as a share of need) over (members, shortfall) strata; shortfall is 0 for no people."""
	strata = list(strata)
	people = sum(members for members, _shortfall in strata)
	if people <= 0.0:
		return 0.0, 0.0
	return people, sum(members * shortfall for members, shortfall in strata) / people


def draw_seed(weather_seed: Any, country: str, kind: str, year: int) -> str:
	"""The text a country's draw for one kind in one year is seeded with."""
	return "%s|%s|%s|%d" % (weather_seed, country, kind, year)


def failed_causes_words(report: Dict[str, Any]) -> str:
	"""Why an event's stated causes do not hold, in the words its data gives."""
	return "; ".join(row["why"] or row["quantity"] for row in report["failed"])


# ---- an event whose causes only partly hold ----

# hazard fields a weakened event shrinks, and how
SCALED_FIELDS = ("sack_chance", "staff_loss", "real_erosion")


def weakened(hazard: Dict[str, Any], strength: float) -> Dict[str, Any]:
    """A copy of the event at `strength` of its size; the original is untouched."""
    adjusted = dict(hazard)
    for field in SCALED_FIELDS:
        if field in adjusted:
            adjusted[field] = adjusted[field] * strength
    if "output_factor" in adjusted:
        adjusted["output_factor"] = 1.0 - (1.0 - adjusted["output_factor"]) * strength
    if isinstance(adjusted.get("values"), dict):
        adjusted["values"] = {key: (shift * strength if isinstance(shift, (int, float)) else shift)
                              for key, shift in adjusted["values"].items()}
    return adjusted
