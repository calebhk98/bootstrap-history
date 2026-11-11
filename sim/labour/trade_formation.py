"""Where the first people of a trade nobody practises come from (Complaint 644, first stage).

Pure functions on plain records, general for any actor and any trade. Three routes, cheapest first:
migration from areas that hold the trade (limited to their spare hands), conversion by training from the
nearest trades (time set by the share of the new trade's tasks the source does not cover, taught by an actor
that holds the knowledge), and purchase of the bonded where the civilisation allows it. A trade none of them
reaches stays empty.

A trade's task description is derived from the hours recipes book to it: each recipe's hours for the trade are
spread over the recipe's input materials (a recipe with no inputs books them to the thing it extracts). Distance
between trades is the angle between their task shares (Gathmann and Schonberg).
"""
from typing import AbstractSet, Any, Callable, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

TaskShares = Dict[str, float]

SOURCE_TASK_FLOOR_FRACTION = declare(
    "SOURCE_TASK_FLOOR_FRACTION", 0.2, kind="temporary_heuristic",
    unit="fraction of the new trade's full apprenticeship", source=None, confidence="D",
    retire="Complaints/644: a learning curve on output replaces a fixed floor on training time",
    why="The share of a full apprenticeship even a trade whose tasks are all covered by the source still needs "
        "(tools, pace and judgement the task shares do not describe). Chosen, not measured: Gathmann and "
        "Schonberg show moves are mostly short-distance, which argues for a small floor.")
TEACHER_ATTENTION_SHARE = declare(
    "TEACHER_ATTENTION_SHARE", 0.1, kind="temporary_heuristic",
    unit="fraction of a trainee's training hours the teacher is present for", source=None, confidence="D",
    retire="Complaints/644: class size and teacher proficiency from a learning curve",
    why="How much of each trainee's time a teacher spends with them (the inverse of a class size). Chosen so "
        "that teaching stays a real cost against a year of the teacher's hours; Smiles reports Soho could not "
        "educate mechanics as fast as it needed them, which argues it is not small.")


def _hours_by_task(recipes: Mapping[str, Mapping[str, Any]]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """(goods hours, service hours), each {trade: {task: hours}}. A recipe's hours for a trade are split equally over its
    input materials; with no inputs they go to "extract:<first output>". A service recipe with no inputs (`service` set)
    has no material to name its tasks by, so its hours are kept apart."""
    goods: Dict[str, Dict[str, float]] = {}
    services: Dict[str, Dict[str, float]] = {}
    for recipe_id, recipe in recipes.items():
        tasks = sorted(material for material, quantity in (recipe.get("inputs") or {}).items() if quantity)
        is_service = bool(recipe.get("service")) and not tasks
        if not tasks:
            outputs = sorted(recipe.get("outputs") or {})
            tasks = ["extract:" + (outputs[0] if outputs else recipe_id)]
        held = services if is_service else goods
        for trade, booked in (recipe.get("labour_hours") or {}).items():
            if booked <= 0:
                continue
            by_task = held.setdefault(trade, {})
            for task in tasks:
                by_task[task] = by_task.get(task, 0.0) + booked / len(tasks)
    return goods, services


def _normalised(by_task: Mapping[str, float]) -> TaskShares:
    total = sum(by_task.values())
    return {task: value / total for task, value in by_task.items()}


def task_shares_by_trade(recipes: Mapping[str, Mapping[str, Any]], taught_from: Optional[Mapping[str, str]] = None) -> Dict[str, TaskShares]:
    """{trade: {task: share of the trade's booked hours}} from recipes with `labour_hours` and `inputs`. A recipe's hours
    for a trade are split equally over its input materials; with no inputs they go to "extract:<first output>". The hours
    of a service with no inputs (an attended hour, a carried load) name no material, so they are done with the goods tasks
    of the trade it is taught from (`taught_from`: {trade: parent trade}); a trade with no such parent, or a parent with
    no goods work, keeps the service as a task of its own. Shares of a trade sum to one."""
    taught_from = taught_from or {}
    goods, services = _hours_by_task(recipes)
    parents = {trade: _normalised(by_task) for trade, by_task in goods.items()}
    shares = {}
    for trade in sorted(set(goods) | set(services)):
        tasks = dict(goods.get(trade, {}))
        parent_tasks = parents.get(taught_from.get(trade, ""), {})
        for task, hours in services.get(trade, {}).items():
            if parent_tasks:
                for parent_task, share in parent_tasks.items():
                    tasks[parent_task] = tasks.get(parent_task, 0.0) + hours * share
            else:
                tasks[task] = tasks.get(task, 0.0) + hours
        shares[trade] = _normalised(tasks)
    return shares


_shares_kept: List[Any] = []     # [production, links, shares] of the last call


_derived: Dict[Callable, Tuple[Mapping[str, Any], Any]] = {}


def _derived_from(builder: Callable, production: Mapping[str, Any]) -> Any:
    """`builder(production)`, kept for the last production graph it was built from. The cache is keyed on the graph
    object itself, so a different mod set (a different graph) is rebuilt, never served stale."""
    held = _derived.get(builder)
    if held is not None and held[0] is production:
        return held[1]
    result = builder(production)
    _derived[builder] = (production, result)
    return result


def task_shares_for(production: Mapping[str, Any], taught_from: Optional[Mapping[str, str]] = None) -> Dict[str, TaskShares]:
    """Task shares of every trade in `production`, the production graph the game loads, with the registry's `taught_from`
    links. Kept for the last graph and links, so a different mod set or registry is rebuilt, never served stale."""
    links = tuple(sorted((taught_from or {}).items()))
    if _shares_kept and _shares_kept[0] is production and _shares_kept[1] == links:
        return _shares_kept[2]
    shares = task_shares_by_trade(production, dict(links))
    _shares_kept[:] = [production, links, shares]
    return shares


SOCIETY = "society"          # the teacher of a trade whose techniques the society already knows
UNGATED = ""                 # marks a recipe that needs no technology


def gating_nodes_by_trade(recipes: Mapping[str, Mapping[str, Any]]) -> Dict[str, FrozenSet[str]]:
    """{trade: nodes whose knowledge the trade's work needs}: the `requires_node` of every recipe that books
    hours to the trade. A recipe that needs no technology (null) contributes `UNGATED`; a recipe that does
    not classify its node (key absent) contributes nothing."""
    nodes: Dict[str, set] = {}
    for recipe in recipes.values():
        if "requires_node" not in recipe:
            continue
        gate = recipe["requires_node"] or UNGATED
        for trade, booked in (recipe.get("labour_hours") or {}).items():
            if booked > 0:
                nodes.setdefault(trade, set()).add(gate)
    return {trade: frozenset(gates) for trade, gates in nodes.items()}


def gating_nodes_for(production: Mapping[str, Any]) -> Dict[str, FrozenSet[str]]:
    """`gating_nodes_by_trade` of the production graph the game loads."""
    return _derived_from(gating_nodes_by_trade, production)


def teachers_of(trade: str, gating: Mapping[str, AbstractSet[str]], knowledge_by_actor: Mapping[str, AbstractSet[str]],
                baseline: AbstractSet[str] = frozenset(), demonstrated: AbstractSet[str] = frozenset()) -> List[str]:
    """The actors that can teach `trade`: those holding the knowledge of any technique its work needs, by
    actor id. A trade with a technique needing no technology, or one the society already knows, has
    `SOCIETY` as a teacher. A technique someone has demonstrated that no listed actor holds still has
    a holder, named "demonstrated". Empty when no one holds any of it."""
    needed = set(gating.get(trade, ()))
    if not needed:
        return []
    teachers = sorted(actor for actor, known in knowledge_by_actor.items() if needed & set(known))
    if UNGATED in needed or needed & set(baseline):
        teachers.insert(0, SOCIETY)
    elif not teachers and needed & set(demonstrated):
        teachers.append("demonstrated")
    return teachers


def uncovered_share(new_trade: Mapping[str, float], source: Mapping[str, float]) -> float:
    """The share of the new trade's tasks the source trade does not already do: one minus the overlap of the
    two sets of shares. With no description of the new trade nothing is covered."""
    if not new_trade:
        return 1.0
    covered = sum(min(share, source.get(task, 0.0)) for task, share in new_trade.items())
    return max(0.0, min(1.0, 1.0 - covered))


def training_years(full_apprenticeship_years: float, uncovered: float) -> float:
    """Years to train a person of the source trade into the new one: a floor of the full apprenticeship plus the
    rest in proportion to the uncovered share of tasks."""
    floor = SOURCE_TASK_FLOOR_FRACTION
    return max(0.0, full_apprenticeship_years) * (floor + (1.0 - floor) * max(0.0, min(1.0, uncovered)))


def teacher_hours_per_person(years: float, hours_per_year: float) -> float:
    """The teacher's own hours to bring one trainee through `years`."""
    return years * hours_per_year * TEACHER_ATTENTION_SHARE


def nearest_sources(new_trade: str, shares: Mapping[str, TaskShares],
                    candidates: Sequence[str]) -> List[Tuple[float, str]]:
    """(uncovered share, trade) for every candidate other than the new trade, least uncovered first, ties by id."""
    described = shares.get(new_trade, {})
    return sorted((uncovered_share(described, shares.get(source, {})), source)
                  for source in candidates if source != new_trade)
