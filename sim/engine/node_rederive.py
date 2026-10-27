"""Keep the tree's derived revenue and upkeep at the techniques the civilisation holds now.

The figures are derived at the gate technologies held (`node_revenue.for_civilisation`, which caches
per held gate set); research that adds a gate changes what can be made and at what cost, so the Sim
re-derives when that set changes.

Composition code, not a module's: it replaces `Sim.nodes`, the one tree object every module reads through the `legacy_tree` view,
and shares `opening_money.priced_nodes` and the wage schedule with the opening's repricing, so it moves with the tree itself.
"""
from sim.prices.api import prices as price_solver
from . import money_units, opening_money
from sim.production.api import node_revenue
from .wage_schedule import build_schedule


def held_gate_set(held_techs):
    return frozenset(price_solver.all_gate_nodes()) & frozenset(held_techs)


def remember_derived_gates(sim, held_techs):
    sim._derived_gate_set = held_gate_set(held_techs)


def refresh_derived_nodes(sim):
    """Re-derive node revenue and upkeep when the gate technologies the society holds (not the founder's
    own completions, which spread by imitation and disclosure) differ from the last derivation."""
    held = sim._society_held_techs()
    gates = held_gate_set(held)
    if gates == sim._derived_gate_set:
        return
    from .data import TRADE_REGISTRY
    schedule = build_schedule(TRADE_REGISTRY, sim.start_civ)
    derived = node_revenue.for_civilisation(sim.nodes, sim.start_civ, schedule, held_techs=held)
    money_units.price_nodes(derived.values(), schedule.wages_per_hour(), schedule.money_per_labour_hour)
    sim.nodes = opening_money.priced_nodes(sim, derived, schedule)
    sim.state.economy.nodes_money_per_labour_hour = schedule.money_per_labour_hour
    sim._derived_gate_set = gates
    # revenue, upkeep and capability_factor memos were read from the old figures
    sim._done_changed()
    sim._operating_changed()
