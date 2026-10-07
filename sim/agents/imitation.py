"""Copying a demonstrated invention: what it takes and how it proceeds.

Pure functions over an actor and a world view. The work goes through wages,
money and calendar time like any project, and it can fail.
"""
import math
from typing import Any, Dict, List, Optional

from . import ledger
from .edges import EDGE_WORKERS
from .tuning import COPY_EFFORT_SHARE, COPY_RISK_SHARE, COPY_TIME_SHARE, HIRING_PREMIUM


def missing_chain(node_id: str, world: Any, actor: Any) -> Optional[List[str]]:
	"""Unknown steps needed to reach `node_id`, prerequisites first.

	None if a prerequisite is neither known to the actor nor demonstrated by
	the founder, so there is nothing to copy it from.
	"""
	demonstrated = world.demonstrated()
	chain: List[str] = []
	seen = set()

	def visit(current: str) -> bool:
		if current in seen:
			return True
		seen.add(current)
		if actor.knows(current, world):
			return True
		if current not in demonstrated:
			return False
		for prerequisite in world.nodes[current].get("pre") or ():
			if not visit(prerequisite):
				return False
		chain.append(current)
		return True

	return chain if visit(node_id) else None


def copy_plan(actor: Any, chain: List[str], world: Any) -> Dict[str, Any]:
	"""Hours, money and calendar for copying every step of `chain`."""
	hours: Dict[str, float] = {}
	pioneer_cost = 0.0
	years = 0.0
	for step in chain:
		node = world.nodes[step]
		for trade, amount in (node.get("lab") or {}).items():
			hours[trade] = hours.get(trade, 0.0) + amount * COPY_EFFORT_SHARE
		pioneer_cost += world.copy_cost(step)
		years = max(years, float(node.get("yrs") or 0.0))
	base_labour = sum(amount * world.labour_market.quote(trade, 0.0, actor) for trade, amount in hours.items())
	premium = sum(amount * world.labour_market.quote(trade, 0.0, actor) * HIRING_PREMIUM
				  for trade, amount in hours.items() if actor.workforce.get(trade, 0.0) <= 0)
	other_money = max(0.0, pioneer_cost * COPY_EFFORT_SHARE - base_labour)
	return {
		"hours": hours,
		"money": other_money + premium,
		"labour_cost": base_labour,
		"total": other_money + premium + base_labour,
		"years": max(1, int(math.ceil(years * COPY_TIME_SHARE))),
	}


def copy_chance(chain: List[str], world: Any) -> float:
	"""Probability the copy succeeds: every step must."""
	chance = 1.0
	for step in chain:
		chance *= 1.0 - min(1.0, world.copy_risk(step) * COPY_RISK_SHARE)
	return chance


def start_work(node_id: str, chain: List[str], plan: Dict[str, Any], year: int) -> Dict[str, Any]:
	"""A new copy project, as stored on the actor."""
	return {"chain": list(chain), "hours": dict(plan["hours"]), "money": plan["money"],
			"labour_cost": plan["labour_cost"], "years": plan["years"],
			"progress": 0.0, "started": year, "stalled": 0.0}


def work_year(actor: Any, node_id: str, work: Dict[str, Any], world: Any) -> bool:
	"""Advance one copy by a year, paying wages and money for what is done.

	Returns True when the work has reached completion. Money that falls short
	slows the work proportionally; nothing is forgiven.
	"""
	step = 1.0 / work["years"]
	want = min(step, 1.0 - work["progress"])
	cost = want * (work["money"] + work["labour_cost"])
	if cost > 0:
		affordable = min(1.0, actor.spendable(world) / cost)
	else:
		affordable = 1.0
	done = want * affordable
	ledger.transfer(actor, world.edge(EDGE_WORKERS), done * (work["money"] + work["labour_cost"]), "copying")
	for trade, amount in work["hours"].items():
		actor.workforce[trade] = actor.workforce.get(trade, 0.0) + (
			amount * done / world.hours_per_person_year)
	if affordable < 1.0:
		work["stalled"] += 1.0
	work["progress"] += done
	return work["progress"] >= 1.0 - 1e-9
