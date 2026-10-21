"""Staged adoption: aware, trying, adopted, with a share of production that follows realised margin.

An actor that knows a technique (it can make it) and is aware of it starts a trial on a pilot share, if it has
what the trial needs from the market or its own stock. After the trial it judges the realised margin against
its incumbent one: a technique that beats it becomes adopted and its share follows the logistic form
share' = speed * gap * share * (1 - share), where the gap is the relative margin over the old technique.
Griliches (1957) fits logistic curves to adoption and ties their slope to profitability
(read: acawiki.org/Hybrid_corn:_An_exploration_in_the_economics_of_technological_change, a summary of the paper;
the slope constant is a labelled heuristic). A technique that does not pay is dropped, unless the actor's state
subsidises the trial or mandates a share, both through the state's levers and paid from its treasury.
Pure functions over an actor and a world view; the actor keeps `adoption`, node id -> {stage, share, since}.
"""
from typing import Any, Dict, Iterable, List

from . import ledger
from .tuning_adoption import ADOPTION_SPEED_PER_MARGIN_GAP, PILOT_SHARE, TRIAL_YEARS

TRYING, ADOPTED = "trying", "adopted"
TRIAL_SUBSIDY, TECH_MANDATE = "trial_subsidy", "tech_mandate"   # lever kinds (government_levers.py)


def margin_gap(new_margin: float, old_margin: float) -> float:
	"""Relative margin of the new technique over the old, in -1..1; 0 when neither makes anything."""
	scale = abs(new_margin) + abs(old_margin)
	return 0.0 if scale <= 0.0 else (new_margin - old_margin) / scale


def next_share(share: float, gap: float) -> float:
	"""One year of the logistic: a share grows when the gap is positive and shrinks when it is negative."""
	return min(1.0, max(0.0, share + ADOPTION_SPEED_PER_MARGIN_GAP * gap * share * (1.0 - share)))


def stage_of(actor: Any, node_id: str) -> str:
	"""unaware, aware (knows it exists), trying or adopted."""
	entry = actor.adoption.get(node_id)
	if entry is not None:
		return entry["stage"]
	return "aware" if node_id in actor.aware else "unaware"


def share_of(actor: Any, node_id: str) -> float:
	entry = actor.adoption.get(node_id)
	return 0.0 if entry is None else float(entry["share"])


def observed_gap(actor: Any, node_id: str, world: Any) -> float:
	"""Margin of the technique (the actor's own when it runs it, else what the economy shows) over the mean
	margin of the actor's other concerns."""
	own = actor.margin_of(node_id)
	new_margin = float(world.concern_margin(node_id)) if own is None else float(own)
	others = [actor.margin_of(other) for other in sorted(actor.concerns) if other != node_id]
	others = [margin for margin in others if margin is not None]
	return margin_gap(new_margin, sum(others) / len(others) if others else 0.0)


def trial_refusals(actor: Any, node_id: str, world: Any) -> List[str]:
	"""Causes that stop a trial: unaware, not skilled, or materials neither sold nor held by the actor."""
	causes = []
	if node_id not in actor.aware and not actor.knows(node_id, world):
		causes.append("unaware")
	if not actor.knows(node_id, world):
		causes.append("skill_unknown")
	if world.unsold_materials(actor, node_id):
		causes.append("materials_unsold")
	return causes


def pay(government: Any, actor: Any, amount: float, purpose: str) -> float:
	"""The state pays what its treasury holds of `amount`; the money paid."""
	paid = min(amount, max(0.0, government.money))
	if paid > 0.0 and government is not actor:
		ledger.transfer(government, actor, paid, purpose)
	return paid


def advance_actor(actor: Any, world: Any) -> List[str]:
	"""One year for one actor: begin trials, judge them, move shares; subsidies and mandates paid by its state.
	Returns "stage:node" events in order."""
	events = []
	candidates = [node_id for node_id in sorted(actor.knowledge - world.baseline_knowledge()) if node_id in world.nodes]
	if not candidates:
		return events
	government = world.government()
	record = getattr(government, "record", None)
	levers: Dict[str, Any] = {} if record is None else record.levers
	subsidies, mandates = levers.get(TRIAL_SUBSIDY) or {}, levers.get(TECH_MANDATE) or {}
	for node_id in candidates:
		gap = observed_gap(actor, node_id, world)
		entry = actor.adoption.get(node_id)
		if entry is None:
			wanted = node_id in subsidies or node_id in mandates or gap > 0.0
			if wanted and not trial_refusals(actor, node_id, world):
				actor.adoption[node_id] = {"stage": TRYING, "share": PILOT_SHARE, "since": world.year}
				events.append("trying:" + node_id)
			continue
		if entry["stage"] == TRYING:
			if node_id in subsidies:
				pay(government, actor, float(subsidies[node_id]), "trial subsidy")
			if world.year - entry["since"] < TRIAL_YEARS:
				continue
			if gap > 0.0 or node_id in mandates:
				entry["stage"] = ADOPTED
				events.append("adopted:" + node_id)
			else:
				del actor.adoption[node_id]
				events.append("dropped:" + node_id)
			continue
		entry["share"] = next_share(entry["share"], gap)
		if node_id in mandates:
			entry["share"] = max(entry["share"], float(mandates[node_id]))
			own = actor.margin_of(node_id)
			if own is not None and own < 0.0:
				pay(government, actor, -own, "mandate compensation")
	return events


def advance(actors: Iterable[Any], world: Any) -> List[str]:
	"""Adoption for every actor, in id order; "actor:event" for each change."""
	found = []
	for actor in sorted(actors, key=lambda each: each.identity()):
		found += ["%s:%s" % (actor.identity(), event) for event in advance_actor(actor, world)]
	return found
