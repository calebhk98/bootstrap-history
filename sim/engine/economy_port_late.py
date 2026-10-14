"""What techniques the society gains after the opening add to the agent economy's opening values.

Part of the port. The opening fixes the recipes the economy's producers can run; the techniques some
producer in the society runs later (the founder's, any firm's concerns) allow more entries. This builds
the opening values with those entries, their trades' wages and the prices of goods that had none; the
economy is then given what it lacks from a setup built from them (`AgentEconomy.admit_techniques`), the
same setup a resumed game builds from its saved opening.
"""
from .economy_port_setup import allowed_entries


def techniques_held(sim):
    """The nodes whose entries the economy's producers may run: those the society started with or was
    granted, and those some producer in it runs now (any seat's, any firm's concerns)."""
    return frozenset(sim.state.projects.granted) | frozenset(sim.techniques_in_use())


def opening_with_techniques(sim, opening, held_nodes, production):
    """`opening` with the entries `held_nodes` allow that it lacks, their trades' wages and the engine's
    prices of the goods they touch that it had none for; None when they add nothing."""
    known = set(opening["recipes"])
    added = [entry_id for entry_id in allowed_entries(production, held_nodes) if entry_id not in known]
    if not added:
        return None
    touched = set()
    trades = set()
    for entry_id in added:
        entry = production[entry_id]
        touched.update(entry.get("outputs") or {}, entry.get("inputs") or {})
        trades.update(entry.get("labour_hours") or {})
    engine_prices = sim._material_prices()
    prices = dict(opening["prices"])
    prices.update({good: engine_prices[good] for good in sorted(touched)
                   if good not in prices and engine_prices.get(good, 0.0) > 0.0})
    wages = dict(opening["wages"])
    for trade in sorted(trades - set(wages)):
        wage = sim.economy.labour.quote(trade)
        if wage > 0.0:
            wages[trade] = wage
    grown = dict(opening)
    grown["recipes"] = sorted(known.union(added))
    grown["prices"] = prices
    grown["wages"] = wages
    return grown
