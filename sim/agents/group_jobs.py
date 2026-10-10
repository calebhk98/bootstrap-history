"""Workers who lost their jobs: a trade's hours offered and not hired (idle hours in the labour core's clearing)
rose above what its workers had come to expect, and the technique that did the work with fewer of their hands."""
from typing import Any, Dict, List, Optional

from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .sector import Sector
from .tuning_strata import STRATUM_WORKING_SHARE

JOBLESS_WORKERS = "jobless_workers"
# the key under which a stratum remembers the share of its trade's hours it expects to go unhired
IDLE_SHARE = "idle_share"


def idle_share_of(stratum: Any, world: Any) -> Optional[float]:
	"""The share of the stratum's trade's hours the clearing left unhired; None for a stratum with no trade or a
	trade that offered no hours."""
	trade = stratum.record.plan.get("trade")
	if not trade:
		return None
	idle, offered = world.idle_hours_by_trade().get(trade, (0.0, 0.0))
	return idle / offered if offered > 0.0 else None


def remember_idle(strata: List[Any], world: Any) -> None:
	"""Each year the share of hours a trade's workers expect to go unhired moves toward the share that did."""
	for stratum in strata:
		share = idle_share_of(stratum, world)
		if share is None:
			continue
		reference = stratum.record.income_reference.get(IDLE_SHARE)
		stratum.record.income_reference[IDLE_SHARE] = (
			share if reference is None else reference + STRATUM_WELFARE_MEMORY_RATE * (share - reference))


def displacing_technique(trade: str, running: Dict[str, int], nodes: Dict[str, Dict[str, Any]]) -> Optional[str]:
	"""The technique, among those `running` (node id -> year opened), that most recently began doing its
	category's work with a smaller share of its labour in `trade` than the category's other techniques ask
	(TEMPORARY HEURISTIC, CLAUDE.md 4.4: until recipes give each trade's hours per unit of a good, the share of
	a technique's labour hours stands for how much it leans on the trade). None if no running technique does."""
	def share(node: Dict[str, Any]) -> Optional[float]:
		hours = node.get("lab") or {}
		total = sum(hours.values())
		return hours.get(trade, 0.0) / total if total > 0.0 else None

	by_category: Dict[Any, List[float]] = {}
	for node in nodes.values():
		node_share = share(node)
		if node_share is not None:
			by_category.setdefault(node.get("cat"), []).append(node_share)
	candidates = []
	for node_id in sorted(running):
		node = nodes.get(node_id) or {}
		node_share = share(node)
		shares = by_category.get(node.get("cat"), [])
		if node_share is None or not shares:
			continue
		mean_share = sum(shares) / len(shares)
		if mean_share > 0.0 and node_share < mean_share:
			candidates.append((running[node_id], mean_share - node_share, node_id))
	return max(candidates)[2] if candidates else None


def jobless_sectors(strata: List[Any], world: Any) -> List[Sector]:
	"""One sector for each stratum whose trade's unhired share of hours is above what its workers expected:
	the hours that went unhired, as people, are those who lost their jobs, and their loss is the pay of those
	jobs; the cause names the technique that did their work with fewer hands, where one can be told."""
	sectors = []
	for stratum in strata:
		record = stratum.record
		share = idle_share_of(stratum, world)
		reference = record.income_reference.get(IDLE_SHARE)
		if share is None or reference is None:
			continue
		rise = share - reference
		if rise < STRATUM_GRIEVANCE_THRESHOLD:
			continue
		trade = record.plan.get("trade")
		working = record.members * float(record.plan.get("work_share", STRATUM_WORKING_SHARE))
		pay = world.pay_per_person_year(trade)
		technique = world.displacing_technique(trade) or ""
		cause = "%d%% of the hours of %s work now go unhired, against %d%% they had come to expect" % (
			round(100.0 * share), trade, round(100.0 * reference))
		if technique:
			cause += ", since %s does the work with fewer hands" % world.technique_name(technique)
		sectors.append(Sector(JOBLESS_WORKERS, record.stratum, "the %s (out of work)" % record.name, cause,
							  rise * working * pay, working * pay, rise * working, 1.0, technique=technique))
	return sectors
