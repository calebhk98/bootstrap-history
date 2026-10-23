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
import functools
import math
from dataclasses import dataclass, field
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from .market.formation import migration_takes, spare_people

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


def task_shares_by_trade(recipes: Mapping[str, Mapping[str, Any]]) -> Dict[str, TaskShares]:
    """{trade: {task: share of the trade's booked hours}} from recipes with `labour_hours` and `inputs`. A
    recipe's hours for a trade are split equally over its input materials; with no inputs they go to
    "extract:<first output>". Shares of a trade sum to one."""
    hours: Dict[str, Dict[str, float]] = {}
    for recipe_id, recipe in recipes.items():
        inputs = sorted(material for material, quantity in (recipe.get("inputs") or {}).items() if quantity)
        if not inputs:
            outputs = sorted(recipe.get("outputs") or {})
            inputs = ["extract:" + (outputs[0] if outputs else recipe_id)]
        for trade, booked in (recipe.get("labour_hours") or {}).items():
            if booked <= 0:
                continue
            by_task = hours.setdefault(trade, {})
            for task in inputs:
                by_task[task] = by_task.get(task, 0.0) + booked / len(inputs)
    shares = {}
    for trade, by_task in hours.items():
        total = sum(by_task.values())
        shares[trade] = {task: value / total for task, value in by_task.items()}
    return shares


@functools.lru_cache(maxsize=1)
def shipped_task_shares() -> Dict[str, TaskShares]:
    """Task shares of every trade, derived from the production data the game loads."""
    from .labour_market import production_data
    return task_shares_by_trade(production_data())


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


@functools.lru_cache(maxsize=1)
def shipped_gating_nodes() -> Dict[str, FrozenSet[str]]:
    from .labour_market import production_data
    return gating_nodes_by_trade(production_data())


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


def teacher_present(trade: str, gating: Mapping[str, AbstractSet[str]], knowledge_by_actor: Mapping[str, AbstractSet[str]],
                    baseline: AbstractSet[str] = frozenset(), demonstrated: AbstractSet[str] = frozenset()) -> bool:
    """Whether any actor holds the knowledge to teach `trade` (see `teachers_of`)."""
    return bool(teachers_of(trade, gating, knowledge_by_actor, baseline, demonstrated))


def task_distance(first: Mapping[str, float], second: Mapping[str, float]) -> float:
    """One minus the cosine between two task descriptions: zero for the same shares, one for none in common.
    Symmetric. A trade with no recorded tasks is at distance one from everything."""
    dot = sum(value * second.get(task, 0.0) for task, value in first.items())
    norm = math.sqrt(sum(value * value for value in first.values())) * math.sqrt(sum(value * value for value in second.values()))
    if norm <= 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - dot / norm))


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


@dataclass
class Route:
    kind: str                  # "migration", "conversion" or "bonded"
    source: str                # an area, a trade, or the bonded market
    people: float
    years: float = 0.0         # time until they work in the new trade
    teacher_hours: float = 0.0


@dataclass
class FormationPlan:
    trade: str
    wanted: float
    routes: List[Route] = field(default_factory=list)

    @property
    def people(self) -> float:
        return sum(route.people for route in self.routes)

    @property
    def empty(self) -> bool:
        return self.people <= 0.0


def first_people_plan(trade: str, wanted: float, *, shares: Mapping[str, TaskShares],
                      full_years: Mapping[str, float], hours_per_worker_year: float,
                      migrant_spare: Mapping[str, float], source_spare: Mapping[str, float],
                      teacher_present: bool, bonded_available: float = 0.0,
                      migration_years: Optional[Mapping[str, float]] = None) -> FormationPlan:
    """Where `wanted` people of `trade` come from, cheapest route first.

    `migrant_spare`: spare hands of this trade by origin area (see `spare_people`); they arrive already
    skilled, so no teacher is needed, and `migration_years` (default none) is the move's time.
    `source_spare`: spare people by other trade, nearest by task distance first; each converts at a time set by the
    uncovered share, and only if `teacher_present` (an actor holding the knowledge exists).
    `bonded_available`: bonded people of the trade the civilisation lets the actor buy (zero where its data forbids it).
    A trade reached by none of these has an empty plan."""
    plan = FormationPlan(trade, wanted)
    remaining = wanted
    for area, take in migration_takes(wanted, migrant_spare):
        plan.routes.append(Route("migration", area, take, (migration_years or {}).get(area, 0.0)))
        remaining -= take
    if remaining > 0.0 and teacher_present:
        for uncovered, source in nearest_sources(trade, shares, sorted(source_spare)):
            take = min(remaining, max(0.0, source_spare[source]))
            if take <= 0.0:
                continue
            years = training_years(full_years.get(trade, 0.0), uncovered)
            plan.routes.append(Route("conversion", source, take, years,
                                     take * teacher_hours_per_person(years, hours_per_worker_year)))
            remaining -= take
            if remaining <= 0.0:
                break
    if remaining > 0.0 and bonded_available > 0.0:
        take = min(remaining, bonded_available)
        plan.routes.append(Route("bonded", "bonded market", take))
    return plan
