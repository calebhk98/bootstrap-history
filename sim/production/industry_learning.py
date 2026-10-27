"""What a concern's experience does to its running, from the tenure stock (Complaint 111). Pure functions.

Scrap and labour per unit fall along an experience curve on the stock of worker-years, toward the figure
the production entry states (the entry states what an established concern does). Plant repair takes the
trades that know the technique; a concern short of them loses running time in proportion. Inputs come from
producers that may be far off and may run shallow industries of their own.
"""
import math
from typing import Dict, Mapping, Optional

from sim.constants import declare

LEARNING_PROGRESS_RATIO = declare(
    "LEARNING_PROGRESS_RATIO", 0.85, kind="temporary_heuristic",
    unit="unit labour after a doubling of cumulative worker-years, over before", confidence="D",
    source="Wright 1936, J. Aeronautical Sciences 3; Argote and Epple 1990, Science 247",
    why="Unit labour and scrap fall by a fixed share for each doubling of cumulative output; Wright found "
        "about four fifths in airframes and Argote and Epple report typical manufacturing ratios of "
        "four fifths to nine tenths. One ratio for every technique until a per-trade one is measured.")


def learning_multiplier(experience, founding_worker_years, mastery_worker_years):
    """Labour per unit, and scrap per unit, over the entry's stated figure: one for a concern whose industry
    holds a mastery's worth of worker-years, rising along the curve toward a first-of-its-kind concern, which
    holds one year of its own staff."""
    exponent = -math.log2(LEARNING_PROGRESS_RATIO)
    held = max(experience, founding_worker_years, 1e-9)
    return max(1.0, (mastery_worker_years / held) ** exponent)


def learning_value_ratio(net_value, purchases_value, labour_hours, multiplier):
    """Net sales (priced in labour hours) once scrap and unit labour run at `multiplier` over the stated
    figures, over net sales at the stated figures: the extra inputs and hours come off what is left."""
    if net_value <= 0.0:
        return 1.0
    extra = (multiplier - 1.0) * (purchases_value + labour_hours)
    return max(0.0, net_value - extra) / net_value


def repair_hours_by_trade(plant) -> Dict[str, float]:
    """Hours a year each trade spends keeping the plant up: the build labour of every capital good the
    concern uses, spread over its stated service life, in proportion to the share of it in use."""
    hours: Dict[str, float] = {}
    for capital, used in plant:
        life = capital.get("service_life_years") or 0.0
        if life <= 0.0:
            continue
        for trade, build_hours in (capital.get("build_labour_hours") or {}).items():
            hours[trade] = hours.get(trade, 0.0) + used * build_hours / life
    return hours


def work_hours_by_trade(labour_hours: Mapping[str, float], repair_hours: Mapping[str, float]) -> Dict[str, float]:
    """Hours a year each trade works in the concern: running it and repairing it."""
    hours = dict(labour_hours)
    for trade, repair in repair_hours.items():
        hours[trade] = hours.get(trade, 0.0) + repair
    return hours


def running_availability(labour_hours: Mapping[str, float], repair_hours: Mapping[str, float],
                         tenure_by_trade: Mapping[str, float]) -> float:
    """Share of the year the concern runs. A trade whose share of the technique's tenure falls short of its
    share of the concern's work cannot do all its repairs; the repairs left undone wait, and the plant
    stands in proportion to the hours of work they are against the hours of running."""
    work = work_hours_by_trade(labour_hours, repair_hours)
    total_work = sum(work.values())
    held = sum(tenure_by_trade.values())
    run_hours = sum(labour_hours.values())
    if total_work <= 0.0 or run_hours <= 0.0 or not repair_hours:
        return 1.0
    undone = 0.0
    for trade, repair in repair_hours.items():
        needed_share = work[trade] / total_work
        held_share = tenure_by_trade.get(trade, 0.0) / held if held > 0.0 else 0.0
        undone += repair * max(0.0, 1.0 - held_share / needed_share)
    return run_hours / (run_hours + undone)


def input_availability(purchases_value: Mapping[str, float], depth_of_input: Mapping[str, float],
                       lead_years_of_input: Mapping[str, Optional[float]]) -> float:
    """Share of the year the concern has its inputs. A shipment in transit cannot be counted on in the
    measure that its supplier's industry is not established: each input costs running time of its
    purchase-value share times the years it takes to arrive times one less its suppliers' depth. An input
    nobody in the economy makes (lead None) is the concern's own or imported, and is not counted here."""
    total = sum(purchases_value.values())
    if total <= 0.0:
        return 1.0
    lost = 0.0
    for material, value in purchases_value.items():
        lead = lead_years_of_input.get(material)
        if lead is not None:
            lost += value / total * min(1.0, lead) * (1.0 - depth_of_input.get(material, 0.0))
    return max(0.0, 1.0 - lost)
