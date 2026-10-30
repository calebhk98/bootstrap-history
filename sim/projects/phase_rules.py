"""The rules of the year's automatic start of projects, as functions of the figures they use."""
from typing import Any, Callable, Dict, List, Sequence

MIN_SURPLUS_FLOOR = 400.0
MIN_SURPLUS_SHARE_OF_FIXED = 0.25


def max_active_projects(base: float, director_pool: float, hours_per_extra_project: float, scholars: float,
                        scholars_per_extra_project: float, artisans: float, artisans_per_extra_project: float) -> int:
    """How many projects can be in hand at once: more directors, scholars and artisans mean more things at once.
    More than this divides the same purse into smaller annual payments, so everything crawls."""
    return int(base + director_pool / hours_per_extra_project + scholars / scholars_per_extra_project
               + artisans / artisans_per_extra_project)


def money_is_thin(revenue: float, fixed_costs: float) -> bool:
    """Whether the surplus after fixed costs is too thin to chase the goal order: the household earns a living first."""
    return revenue - fixed_costs < max(MIN_SURPLUS_FLOOR, fixed_costs * MIN_SURPLUS_SHARE_OF_FIXED)


def candidates_in_order(order: Sequence[str], node_of: Callable[[str], Dict[str, Any]], project_cost: Callable[[str], float],
                        thin_money: bool) -> List[str]:
    """The nodes the automatic start walks. With thin money, whatever pays best for what it costs comes first
    (revenue over cost), then the rest in goal order; otherwise the goal order."""
    if not thin_money:
        return list(order)
    earners = [node_id for node_id in order if node_of(node_id)["rev"] - node_of(node_id)["up"] > 0]
    earners.sort(key=lambda node_id: project_cost(node_id) / max(1.0, node_of(node_id)["rev"] - node_of(node_id)["up"]))
    earner_set = set(earners)
    return earners + [node_id for node_id in order if node_id not in earner_set]


def non_bountied_count(active: Sequence[str], bountied: Any) -> int:
    """Projects in hand that were not bought as a prize; a bounty never counts against the cap."""
    return len(active) - len(set(bountied) & set(active))
