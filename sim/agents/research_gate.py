"""The start gates of a piece of research, one set for every actor and the founder's seat.

Each gate is a pure function of a node and plain answers (what the researcher knows, what hands it has). The
founder's start check and `refusals` for any other actor call the same functions, so a node is open to one
exactly when the same facts would open it to the other.
"""
from typing import Any, Callable, Dict, List, Optional

from sim.refusal import Refusal

from . import awareness
from .no_country_economy import NoCountryEconomy

SCHOLAR_FAMILY = "scholar"
SCHOLAR_TRADE = "scholar"
CRAFT_FAMILY = "craft"


def unmet_prerequisites(node: Dict[str, Any], knows: Callable[[str], bool]) -> List[str]:
	return [prerequisite for prerequisite in node.get("pre") or () if not knows(prerequisite)]


def substitute_quality(node: Dict[str, Any], group: Dict[str, Any], has_option: Callable[[str], bool],
					   is_technique: Callable[[str], bool], purchasable_discount: float) -> float:
	"""The best quality one `req_any` group offers: an option the researcher has (a technique it knows or a
	material the node buys), or a plain commodity bought off the market at a discount."""
	best = 0.0
	for option, quality in (group.get("options") or {}).items():
		if has_option(option) or option in (node.get("mat") or {}):
			best = max(best, float(quality))
		elif not is_technique(option):
			best = max(best, float(quality) * purchasable_discount)
	return best


def unserved_substitute_group(node: Dict[str, Any], has_option: Callable[[str], bool],
							  is_technique: Callable[[str], bool], purchasable_discount: float) -> Optional[Dict[str, Any]]:
	"""The first `req_any` group no option serves, or None when every group is served."""
	for group in node.get("req_any") or ():
		if substitute_quality(node, group, has_option, is_technique, purchasable_discount) <= 0.0:
			return group
	return None


def materials_short_of_stock(needs_tonnes: Dict[str, float], buyable: Callable[[str], bool],
							 held_tonnes: Callable[[str], float]) -> List[str]:
	"""Materials the researcher cannot get: not for sale in reach and not held in enough tonnes by the researcher
	itself (its own stock, not the founder's), sorted."""
	return [material for material in sorted(needs_tonnes)
			if not buyable(material) and held_tonnes(material) < needs_tonnes[material]]


def hands_short(needed: float, available: float) -> float:
	"""How many trained people short the researcher is of a node's requirement (0 when it has them)."""
	return max(0.0, float(needed) - float(available))


def refusals(actor: Any, node_id: str, world: Any) -> List[Refusal]:
	"""Every reason this actor may not begin researching the node now, each with a `cause` and its `facts`."""
	if node_id not in world.nodes:
		return [Refusal("no_such_node", "no such node")]
	node = world.nodes[node_id]
	if actor.knows(node_id, world):
		return [Refusal("already_known", "already known")]
	if node_id in actor.works:
		return [Refusal("already_being_researched", "already being researched")]
	found: List[Refusal] = []
	if not awareness.knows_it_exists(actor, node_id, world):
		found.append(Refusal("unaware", "has not yet learned that this exists"))
	missing = unmet_prerequisites(node, lambda prerequisite: actor.knows(prerequisite, world))
	if missing:
		found.append(Refusal("prerequisites_unknown", "prerequisites unknown: " + ", ".join(sorted(missing)),
							 missing=sorted(missing)))
	group = unserved_substitute_group(node, lambda option: actor.knows(option, world),
									  lambda option: option in world.nodes, world.purchasable_substitute_discount())
	if group is not None:
		found.append(Refusal("no_substitute", "nothing that would serve: any of %s"
							 % ", ".join(sorted(group.get("options") or ())), options=sorted(group.get("options") or ())))
	for family, needed, cause in ((SCHOLAR_FAMILY, node.get("sch") or 0, "scholar_staff"),
								  (CRAFT_FAMILY, node.get("art") or 0, "craft_staff")):
		if needed <= 0:
			continue
		try:
			hands = world.research_hands(actor, family)
		except NoCountryEconomy as error:     # the actor's country keeps no record of its people: it cannot start the work
			found.append(Refusal("no_country_hands", "the actor's country keeps no record of its %s hands" % family,
								 country=error.country, family=family))
			continue
		short = hands_short(needed, hands)
		if short > 0.0:
			found.append(Refusal(cause, "needs %d trained %s, and only %.1f can be put on it" % (
				needed, "scholars" if family == SCHOLAR_FAMILY else "craftsmen", needed - short), needed=needed, short=short))
	unsold = world.unsold_materials(actor, node_id)
	if unsold:
		found.append(Refusal("materials_unsold", "no one in reach sells " + ", ".join(unsold), materials=list(unsold)))
	return found
