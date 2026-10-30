"""Diffusion's rules as plain functions of plain values: staff advice, categories and their pace, tech effects, disclosure."""
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from sim.refusal import Refusal

DISCLOSURE_MODES = ("default", "secret", "license", "publish")


# ---- staff advice ----

def staff_hire_advice(kind: str, count: Optional[int] = None) -> str:
	"""The hire command for `kind`, sized to `count` people when the shortfall is known, else a typical order."""
	if kind == "scholars":
		return ("{\"cmd\":\"hire\",\"trade\":\"scholar\",\"n\":%d} "
		        "hires literate men by the year; see {\"cmd\":\"labour\"}" % (count or 2))
	return ("{\"cmd\":\"hire\",\"trade\":\"smith\",\"n\":%d} or any "
	        "trade in {\"cmd\":\"labour\"}; or "
	        "{\"cmd\":\"commission\",\"trade\":\"smith\",\"hours\":400} "
	        "to buy one job instead of employing anybody" % (count or 3))


def staff_sources(declared: Iterable[Tuple[str, Mapping[str, Any]]]) -> Dict[str, List[Tuple[str, str]]]:
	"""{"scholars"|"artisans": [(node or HIRE/BUY, advice)]}: HIRE first, the nodes declaring `staff_advice`
	(`declared`, in their order), then BUY.

	fin_company_town and fin_chain_store are deliberately not listed for artisans: the advice reader checks each
	named node's visibility, and a node whose prerequisites are blocked on artisans would call back into this list."""
	hire = {kind: ("HIRE", staff_hire_advice(kind)) for kind in ("scholars", "artisans")}
	buy = ("BUY", "{\"cmd\":\"buy\",\"what\":\"slaves\",\"n\":N} then "
	              "manumit, though they are untrained for three years")
	sources = {kind: [entry] for kind, entry in hire.items()}
	for node_id, spec in declared:
		sources[spec["kind"]].append((node_id, spec["advice"]))
	sources["artisans"].append(buy)
	return sources


# ---- a node's know-how ----

def copy_difficulty_of(node: dict) -> float:
	"""How hard a node's know-how is to copy from sight. A node declares `copy_visibility` (the share an onlooker
	can recover from the product or the yard) and difficulty is its reciprocal; a node that does not falls back
	to the trades and materials it needs, at least one (TRANSITIONAL, CLAUDE.md 4.4)."""
	if node.get("copy_visibility"):
		return 1.0 / float(node["copy_visibility"])
	trades = [trade for trade, hours in (node.get("lab") or {}).items() if hours > 0]
	materials = [material for material, amount in (node.get("mat") or {}).items() if amount]
	return max(1, len(trades) + len(materials))


# ---- the categories a node's effects spread by ----

def diffusion_category(traits: Optional[Iterable[str]], trait_names: Iterable[str]) -> Optional[str]:
	"""The first diffusing category (in priority order) among a node's traits, or None."""
	traits = traits or ()
	for trait in trait_names:
		if trait in traits:
			return trait
	return None


def diffusible_ids(nodes: Mapping[str, Mapping[str, Any]], trait_names: Sequence[str]) -> Dict[str, Tuple[str, ...]]:
	"""The node ids of each diffusing category, sorted."""
	found: Dict[str, List[str]] = {category: [] for category in trait_names}
	for node_id, node in nodes.items():
		category = diffusion_category(node.get("traits"), trait_names)
		if category:
			found[category].append(node_id)
	return {category: tuple(sorted(ids)) for category, ids in found.items()}


def text_category_pace(corpus_pace: float, general_literacy: float, literacy_reference: float,
                       pace_base: float, pace_span: float, pace_cap_ratio: float) -> float:
	"""How much faster than its bare half-life a text-paced category (medical, information) moves: a written corpus
	and the country's literacy, as a share of the reference, speed it up."""
	pace = corpus_pace
	pace *= (pace_base + pace_span * min(pace_cap_ratio, general_literacy / max(0.02, literacy_reference)))
	return pace


def category_half_life(bare_half_life_years: float, pace: float, pace_floor: float) -> float:
	"""Years for half of a category's just-completed technology to spread at `pace`."""
	return bare_half_life_years / max(pace_floor, pace)


def diffusion_report(food: float, medical: float, military: float, information: float,
                     medical_relief: Callable[[], float]) -> Optional[Dict[str, float]]:
	"""None while nothing the founder has built is spreading; else how far each category has spread. The relief of
	the next epidemic is asked for only when medicine has spread."""
	if food < 0.01 and medical < 0.01 and military < 0.01 and information < 0.01:
		return None
	out: Dict[str, float] = {}
	if food >= 0.01:
		out["food_and_farming_the_country_has_adopted"] = round(food, 3)
	if medical >= 0.01:
		out["public_health_the_country_has_adopted"] = round(medical, 3)
		out["how_much_softer_the_next_epidemic_will_be"] = round(medical_relief(), 3)
	if military >= 0.01:
		out["military_technology_now_in_the_states_hands"] = round(military, 3)
	if information >= 0.01:
		out["printing_and_literacy_the_country_has_adopted"] = round(information, 3)
	return out


# ---- what a finished technique does to the society ----

def burden_before_effect(burden: float, delta: float, held: Callable[[], float], total_weight: float,
                         counted: bool) -> float:
	"""The disease burden before a disease technology's `delta` was counted: the node's `held` share of its weight
	(asked for only when it counts) comes back off; a node that is not one of the burden's technologies leaves it
	as it is."""
	return min(1.0, burden + delta * held() / total_weight) if total_weight > 0 and counted else burden


def society_changed_text(name: str, changed: Iterable[str]) -> str:
	return "%s changes the society, the whole of it at once rather than one site: %s" % (name, "; ".join(sorted(changed)))


def value_weight_change_text(field: str, before: float, after: float) -> str:
	return "%s %.2f -> %.2f" % (field, before, after)


def burden_change_text(before: float, after: float) -> str:
	return ("population (disease burden %.2f -> %.2f of the pre-industrial level, which slows deaths and "
	        "raises survival from the next year)" % (before, after))


def literacy_change_text(field: str, before: float, after: float) -> str:
	return "%s %.1f%% -> %.1f%% (%+.1f points, one step)" % (field, before * 100, after * 100, (after - before) * 100)


def census_bits(changed: Mapping[str, float]) -> List[str]:
	"""The clauses of the literacy census line for the figures that moved."""
	bits = []
	if "literacy_general" in changed:
		bits.append("general reading is now %d%% of the population" % round(changed["literacy_general"] * 100))
	if "literacy_elite" in changed:
		bits.append("the lettered and propertied class is now %d%% literate" % round(changed["literacy_elite"] * 100))
	return bits


# ---- disclosure ----

def default_disclosure() -> Dict[str, Any]:
	return {"mode": "default", "published_year": None, "licensees": {}}


def disclosure_problem(known: bool, made_here: bool, mode: str, current_mode: str) -> Optional[Dict[str, Any]]:
	"""The refusal of a disclosure choice, or None when it may go ahead."""
	if not known or not made_here:
		return {"ok": False, "error": "you can only choose for an invention you have made yourself"}
	if mode not in DISCLOSURE_MODES[1:]:
		return {"ok": False, "error": "choose secret, license or publish"}
	if current_mode == "publish":
		return {"ok": False, "error": "it is already published; that cannot be taken back"}
	return None


def refusal_reply(problem: Refusal) -> Dict[str, Any]:
	return {"ok": False, "error": str(problem), "cause": problem.cause, "facts": problem.facts}


def disclosure_listing(made: Iterable[str], modes: Mapping[str, Mapping[str, Any]], operating: Iterable[str]) -> List[Dict[str, Any]]:
	"""Every invention of the seat with what it chose for it; `made` are its nodes, sorted here."""
	operating = set(operating)
	return [{"id": node_id, "mode": modes[node_id]["mode"], "licensees": sorted(modes[node_id]["licensees"]),
	         "operating": node_id in operating} for node_id in sorted(made)]
