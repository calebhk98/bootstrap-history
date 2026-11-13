"""`spin-up-trace --stages --ensemble N`: replay one opening N times, member k with its households' cash perturbed at the
rounding level (sim/markets/spin_up_ensemble.py), several members at once in separate processes."""
import concurrent.futures
import os
import random

from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api


def run_member(civilisation_id, member):
    """{"member", "gaps", "trends"} of one replay of the civilisation's opening; None gaps when too few years were measured."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civilisation_id))
    _watched, replayed = markets_api.spin_up_stages(game, markets_api.spin_up_cash_factor(member))
    gaps, trends = markets_api.spin_up_member_figures(list(replayed))
    return {"member": member, "gaps": gaps, "trends": trends}


def run_ensemble(civilisation_id, members, jobs=0):
    """The members' results in member order, `jobs` (default: the cores available) at a time."""
    jobs = min(jobs or os.cpu_count() or 1, members)
    if jobs <= 1:
        return [run_member(civilisation_id, member) for member in range(members)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(run_member, [civilisation_id] * members, range(members)))
