"""Keep the tree's derived revenue and upkeep at the techniques the civilisation holds now.

The figures are derived at the gate technologies held (`node_revenue.for_civilisation`, which caches
per held gate set); research that adds a gate changes what can be made and at what cost, so the Sim
re-derives when that set changes.

Composition code, not a module's: it replaces `Sim.nodes`, the one tree object every module reads through the `legacy_tree` view,
and shares `opening_money`'s opening schedule and pricing with the opening's repricing, so it moves with the tree itself.
"""
from sim.prices.api import prices as price_solver
from . import money_units, opening_money
from sim.production.api import node_revenue


def held_gate_set(held_techs, mods_dir=None):
    return frozenset(price_solver.all_gate_nodes(price_solver.default_production_entries(mods_dir))) & frozenset(held_techs)


def remember_derived_gates(sim, held_techs):
    sim._derived_gate_set = held_gate_set(held_techs, sim.mods_dir)


def refresh_derived_nodes(sim):
    """Re-derive node revenue and upkeep when the gate technologies the society holds (not the founder's
    own completions, which spread by imitation and disclosure) differ from the last derivation."""
    held = sim.view("society_techs")()
    gates = held_gate_set(held, sim.mods_dir)
    if gates == sim._derived_gate_set:
        return
    schedule = opening_money.opening_schedule(sim)
    derived = node_revenue.for_civilisation(sim.nodes, sim.start_civ, schedule, held_techs=held,
                                            unskilled_trade=sim.view("unskilled_trade")(), mods_dir=sim.mods_dir)
    money_units.price_nodes(derived.values(), schedule.wages_per_hour(), schedule.money_per_labour_hour)
    priced = opening_money.priced_schedule(sim, schedule)
    sim.nodes = opening_money.priced_nodes(derived, priced)
    sim.state.economy.nodes_money_per_labour_hour = priced.money_per_labour_hour
    sim._derived_gate_set = gates
    # revenue, upkeep and capability_factor memos were read from the old figures
    sim._done_changed()
    sim._operating_changed()
