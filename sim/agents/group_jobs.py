"""Workers who lost their jobs: a trade's hours offered and not hired (idle hours in the labour core's clearing)
rose above what its workers had come to expect, and the technique that did the work with fewer of their hands."""
from typing import Any, Dict, List, Optional

from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .sector import Sector
from .tuning_strata import STRATUM_WORKING_SHARE

JOBLESS_WORKERS = "jobless_workers"
# the key under which a stratum remembers the share of its trade's hours it expects to go unhired
IDLE_SHARE = "idle_share"


def idle_share_of(stratum: Any, idle_hours: Dict[str, Any]) -> Optional[float]:
	"""The share of the stratum's trade's hours the clearing left unhired, given `idle_hours` (the stakes' idle hours by
	trade, read once by the caller); None for a stratum with no trade or a trade that offered no hours."""
	trade = stratum.record.plan.get("trade")
	if not trade:
		return None
	idle, offered = idle_hours.get(trade, (0.0, 0.0))
	return idle / offered if offered > 0.0 else None


def idle_hours_for(strata: List[Any], world: Any) -> Dict[str, Any]:
	"""The stakes' idle hours by trade, read once for `strata`; read only when some stratum has a trade (the read refuses
	where the country has no economy)."""
	if not any(stratum.record.plan.get("trade") for stratum in strata):
		return {}
	return world.stakes.idle_hours_by_trade()  # type: ignore[no-any-return]


def remember_idle(strata: List[Any], world: Any) -> None:
	"""Each year the share of hours a trade's workers expect to go unhired moves toward the share that did."""
	idle_hours = idle_hours_for(strata, world)
	for stratum in strata:
		share = idle_share_of(stratum, idle_hours)
		if share is None:
			continue
		reference = stratum.record.income_reference.get(IDLE_SHARE)
		stratum.record.income_reference[IDLE_SHARE] = (
			share if reference is None else reference + STRATUM_WELFARE_MEMORY_RATE * (share - reference))


def category_mean_shares(trade: str, nodes: Dict[str, Dict[str, Any]]) -> Dict[Any, float]:
	"""The mean over each category's nodes with any labour (in tree order) of their share of labour hours in
	`trade`. Depends on the tree and the trade only."""
	shares_by_category: Dict[Any, List[float]] = {}
	for node in nodes.values():
		node_share = share_of_trade(node, trade)
		if node_share is not None:
			shares_by_category.setdefault(node.get("cat"), []).append(node_share)
	return {category: sum(shares) / len(shares) for category, shares in shares_by_category.items()}


# the shares for the one tree last asked about, by trade; the tree is replaced, never edited, when it is derived again
_kept: Dict[str, Any] = {"nodes": None, "by_trade": {}}


def kept_category_shares(trade: str, nodes: Dict[str, Dict[str, Any]]) -> Dict[Any, float]:
	"""`category_mean_shares(trade, nodes)`, kept while the same tree object is asked about."""
	if _kept["nodes"] is not nodes:
		_kept["nodes"], _kept["by_trade"] = nodes, {}
	if trade not in _kept["by_trade"]:
		_kept["by_trade"][trade] = category_mean_shares(trade, nodes)
	return _kept["by_trade"][trade]  # type: ignore[no-any-return]


def share_of_trade(node: Dict[str, Any], trade: str) -> Optional[float]:
	"""The share of the node's labour hours that is `trade`; None for a node with no labour."""
	hours = node.get("lab") or {}
	total = sum(hours.values())
	return hours.get(trade, 0.0) / total if total > 0.0 else None


def displacing_technique(trade: str, running: Dict[str, int], nodes: Dict[str, Dict[str, Any]],
						 by_category: Optional[Dict[Any, float]] = None) -> Optional[str]:
	"""The technique, among those `running` (node id -> year opened), that most recently began doing its
	category's work with a smaller share of its labour in `trade` than the category's other techniques ask
	(TEMPORARY HEURISTIC, CLAUDE.md 4.4: until recipes give each trade's hours per unit of a good, the share of
	a technique's labour hours stands for how much it leans on the trade). None if no running technique does.
	`by_category` is `category_mean_shares(trade, nodes)`; without it the shares kept for this tree are used."""
	if by_category is None:
		by_category = kept_category_shares(trade, nodes)
	candidates = []
	for node_id in sorted(running):
		node = nodes.get(node_id) or {}
		node_share = share_of_trade(node, trade)
		mean_share = by_category.get(node.get("cat"))
		if node_share is None or mean_share is None:
			continue
		if mean_share > 0.0 and node_share < mean_share:
			candidates.append((running[node_id], mean_share - node_share, node_id))
	return max(candidates)[2] if candidates else None


def jobless_sectors(strata: List[Any], world: Any, idle_hours: Optional[Dict[str, Any]] = None) -> List[Sector]:
	"""One sector for each stratum whose trade's unhired share of hours is above what its workers expected:
	the hours that went unhired, as people, are those who lost their jobs, and their loss is the pay of those
	jobs; the cause names the technique that did their work with fewer hands, where one can be told. A caller that
	holds the stakes' idle hours by trade passes them as `idle_hours`."""
	if idle_hours is None:
		idle_hours = idle_hours_for(strata, world)
	sectors = []
	for stratum in strata:
		record = stratum.record
		share = idle_share_of(stratum, idle_hours)
		reference = record.income_reference.get(IDLE_SHARE)
		if share is None or reference is None:
			continue
		rise = share - reference
		if rise < STRATUM_GRIEVANCE_THRESHOLD:
			continue
		trade = record.plan.get("trade")
		working = record.members * float(record.plan.get("work_share", STRATUM_WORKING_SHARE))
		pay = world.labour.pay_per_person_year(trade)
		technique = world.stakes.displacing_technique(trade) or ""
		cause = "%d%% of the hours of %s work now go unhired, against %d%% they had come to expect" % (
			round(100.0 * share), trade, round(100.0 * reference))
		if technique:
			cause += ", since %s does the work with fewer hands" % world.stakes.technique_name(technique)
		sectors.append(Sector(JOBLESS_WORKERS, record.stratum, "the %s (out of work)" % record.name, cause,
							  rise * working * pay, working * pay, rise * working, 1.0, technique=technique))
	return sectors
