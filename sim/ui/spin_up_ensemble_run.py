"""`spin-up-trace --stages --ensemble N`: replay one opening N times, member k with its households' cash perturbed at the
rounding level (sim/markets/spin_up_ensemble.py), several members at once in separate processes."""
import concurrent.futures
import os
import random

from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api


LEVEL_PARTS_KEPT = 4     # the goods that moved a member's price level most, kept for the report


def run_member(civilisation_id, member, rules=None):
    """{"member", "gaps", "trends", "by_good" (spin_up_by_good.by_good), "level_parts" (the goods that moved its price
    level most, spin_up_by_good.price_level_parts), "misses" (the quantities it ends over the tolerance on, each with
    the good that moved it most, spin_up_by_good.misses)} of one replay of the civilisation's opening; None gaps when too few years were measured.
    `rules` names the rule set the economy opens on (None: the shipped one)."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civilisation_id),
               cfg=markets_api.rule_set_configuration(rules))
    _watched, replayed = markets_api.spin_up_stages(game, markets_api.spin_up_cash_factor(member))
    rows = list(replayed)
    gaps, trends = markets_api.spin_up_member_figures(rows)
    return {"member": member, "gaps": gaps, "trends": trends, "by_good": markets_api.spin_up_by_good(rows),
            "level_parts": markets_api.spin_up_price_level_parts(rows)[:LEVEL_PARTS_KEPT],
            "misses": markets_api.spin_up_member_misses(rows)}


def run_ensemble(civilisation_id, members, jobs=0, rules=None):
    """The members' results in member order, `jobs` (default: the cores available) at a time, on the rule set `rules`."""
    jobs = min(jobs or os.cpu_count() or 1, members)
    if jobs <= 1:
        return [run_member(civilisation_id, member, rules) for member in range(members)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(run_member, [civilisation_id] * members, range(members), [rules] * members))
