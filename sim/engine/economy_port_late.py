"""What techniques the society gains after the opening add to the agent economy's opening values.

Part of the port. The opening fixes the recipes the economy's producers can run; the techniques some
producer in the society runs later (the founder's, any firm's concerns) allow more entries. This builds
the opening values with those entries, their trades' wages and the prices of goods that had none; the
economy is then given what it lacks from a setup built from them (`AgentEconomy.admit_techniques`), the
same setup a resumed game builds from its saved opening.
"""
from .economy_port_setup import allowed_entries
from sim.prices.api import making_cost
cost_of_making = making_cost.cost_of_making


def techniques_held(sim):
    """The nodes whose entries the economy's producers may run: those the society started with or was
    granted, and those some producer in it runs now (any seat's, any firm's concerns)."""
    return frozenset(sim.state.projects.granted) | frozenset(sim.techniques_in_use())


def late_goods_costs(sim, prices, goods, held_nodes, production):
    """{good: money per unit} the cost of making each good that has no price yet, at the economy's live input
    prices (the opening's where the economy has none) and live wages, the cheapest way the held techniques allow."""
    live = sim.economy.agent_prices() or {}
    wages = {}

    def input_price_of(material):
        price = live.get(material) or prices.get(material)
        return price if price and price > 0.0 else None

    def wage_of(trade):
        if trade not in wages:
            wages[trade] = sim.economy.labour.quote(trade)
        return wages[trade]

    rate = float(sim.economy.base_rate())
    found = {}
    for good in goods:
        if good in prices:
            continue
        made = cost_of_making(good, held_nodes, input_price_of, wage_of, rate, production=production,
                              civilization=sim.civ)
        if made is not None and made.unit_cost > 0.0:
            found[good] = made.unit_cost
    return found


def opening_with_techniques(sim, opening, held_nodes, production):
    """`opening` with the entries `held_nodes` allow that it lacks, their trades' wages and the
    cost of making the goods they touch that it had no price for; None when they add nothing."""
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
    prices = dict(opening["prices"])
    prices.update(late_goods_costs(sim, prices, sorted(touched), held_nodes, production))
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
