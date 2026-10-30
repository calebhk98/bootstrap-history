"""The knowledge module's rules as plain functions of plain values."""
from typing import AbstractSet, Any, Callable, Dict, FrozenSet, Iterable, List, Mapping, NamedTuple, Optional, Tuple


class SeatTechniques(NamedTuple):
    """What one seat holds, and the part of it that its country already had."""
    held: FrozenSet[str]
    granted: FrozenSet[str]


def in_tree_order(nodes: Iterable[str], done: AbstractSet[str]) -> List[str]:
    """The finished nodes in the tree's own order. A set of strings iterates in an order that depends on the process,
    and a float sum over it would differ in its last bits between one run and the next."""
    return [node_id for node_id in nodes if node_id in done]


def reveal_targets(nodes: Mapping[str, Mapping[str, Any]], node_id: str) -> List[str]:
    """`node_id` and every node it leads towards (it is a prerequisite or an option of an alternative group): what
    finishing it teaches the player of, vaguely."""
    targets = [node_id]
    for other, node in nodes.items():
        if node_id in node.get("pre", []):
            targets.append(other)
        for group in node.get("req_any", []):
            if node_id in (group.get("options") or {}):
                targets.append(other)
    return targets


def earliest_done_year(seats: Iterable[Tuple[AbstractSet[str], Optional[Mapping[str, int]]]], node_id: str,
                       default: int) -> int:
    """The year the first seat to hold `node_id` finished it (`default` for a holder with no record, or when no seat
    holds it). Each seat is (the nodes it holds, the year it finished each)."""
    years = [(done_year or {}).get(node_id, default) for done, done_year in seats if node_id in done]
    return min(years) if years else default


def years_to_add(own: Optional[Mapping[str, int]], other: Optional[Mapping[str, int]]) -> Dict[str, int]:
    """The finish years `other` adds to a record `own`: a node only `other` dates, or both date and `other` dates it earlier
    (the earliest year wins, as `earliest_done_year` reads them). Empty when `other` records nothing."""
    own = own or {}
    return {node_id: year for node_id, year in (other or {}).items() if node_id not in own or year < own[node_id]}


def corpus_hedge(tiers: Iterable[Tuple[str, float, float]], held: AbstractSet[str], none_chance: float,
                none_fraction: float) -> Tuple[float, float, Optional[str]]:
    """(loss chance, fraction lost, hedge node) a sacking faces: the first tier, best first, whose node is held (held,
    not running: books exist even when the institution is closed). Nothing held takes the unhedged figures and no node."""
    for node_id, loss_chance, fraction_lost in tiers:
        if node_id in held:
            return loss_chance, fraction_lost, node_id
    return none_chance, none_fraction, None


def never_abandon(category_never_abandoned: bool, relied_on_running: bool, on_road_to_goal: bool) -> bool:
    """Protected from being let go: knowledge of a category flagged never abandoned, and anything the goal needs that
    no running work leans on. Keyed on the goal's road rather than on category names, so a patron can be let go and
    rebuilt later but a step the goal needs is not quietly deleted and then refused funding."""
    if category_never_abandoned:
        return True
    if relied_on_running:
        return False
    return on_road_to_goal


def losable_node_ids(held: Iterable[str], granted: AbstractSet[str], nodes: Mapping[str, Mapping[str, Any]], keep_dispersed: bool,
                     is_dispersed: Callable[[str], bool]) -> List[str]:
    """Held nodes a loss event may take: not inherited, not a measured goal (a measurement cannot be forgotten), and with
    `keep_dispersed` not a dispersed corpus."""
    return sorted(node_id for node_id in held
                  if node_id not in granted
                  and not nodes[node_id].get("win_condition")
                  and not (keep_dispersed and is_dispersed(node_id)))
