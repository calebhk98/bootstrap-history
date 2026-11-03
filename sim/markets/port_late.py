"""What techniques the society gains after the opening add to the agent economy's opening values.

Part of the port. The opening fixes the recipes the economy's producers can run; the techniques some
producer in the society runs later (the founder's, any firm's concerns) allow more entries. This builds
the opening values with those entries, their trades' wages and the prices of goods that had none; the
economy is then given what it lacks from a setup built from them (`AgentEconomy.admit_techniques` (agent_economy.py)), the
same setup a resumed game builds from its saved opening.
"""
from .port_setup import allowed_entries, opening_wages
from sim.prices.api import making_cost, solve_prices_core
cost_of_making = making_cost.cost_of_making


def techniques_held(sim):
    """The nodes whose entries the economy's producers may run: those the society started with or was
    granted, and those some producer in it runs now (any seat's, any firm's concerns)."""
    return sim.production.techniques_granted() | frozenset(sim.production.techniques_in_use())


def late_goods_costs(sim, prices, goods, held_nodes, production, wage_level=1.0):
    """{good: opening-year money per unit} the cost of making each good that has no price yet, at the economy's live
    input prices (the opening's, scaled to today's money, where the economy has none) and live wages, the cheapest way
    the held techniques allow. `wage_level` is today's money per opening-year money."""
    live = sim.economy.agent_prices() or {}
    wages = {}

    def input_price_of(material):
        price = live.get(material)
        if price and price > 0.0:
            return price
        opening = prices.get(material)      # opening-year money: scaled to today's
        return opening * wage_level if opening and opening > 0.0 else None

    registry = sim.state.trade_registry

    def wage_of(trade):
        """The labour market's quote of a trade the game knows; None for one it does not, so a recipe needing it has no cost."""
        if trade not in registry:
            return None
        if trade not in wages:
            wages[trade] = sim.economy.labour.quote(trade)
        return wages[trade]

    def rent_of(key):
        """Coin a hectare-year of land costs where the land market let any; None before it has, which leaves a good that
        occupies land without a cost."""
        return sim.economy.agent_land_rent_per_hectare() if key == solve_prices_core.LAND_MATERIAL else None

    rate = float(sim.finance.market_rate())
    found = {}
    for good in goods:
        if good in prices:
            continue
        made = cost_of_making(good, held_nodes, input_price_of, wage_of, rate, rent_of=rent_of, production=production,
                              civilization=sim.scenario.civ)
        if made is not None and made.unit_cost > 0.0:
            found[good] = made.unit_cost / wage_level
    return found


def opening_with_techniques(sim, opening, held_nodes, production, wage_level):
    """`opening` with the entries `held_nodes` allow that it lacks, their trades' wages (in opening-year money: today's quote over
    `wage_level`, today's money per opening-year money) and the cost of making the goods they touch that it had no price for;
    None when they add nothing."""
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
    prices.update(late_goods_costs(sim, prices, sorted(touched), held_nodes, production, wage_level))
    wages = {**opening["wages"],
             **opening_wages(sim, trades - set(opening["wages"]), wage_level)}
    grown = dict(opening)
    grown["recipes"] = sorted(known.union(added))
    grown["prices"] = prices
    grown["wages"] = wages
    return grown
