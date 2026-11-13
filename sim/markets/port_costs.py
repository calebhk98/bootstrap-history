"""What the agent economy's opening is seeded with: the cost of making every good, nothing else.

Part of the port. `long_run_costs.long_run_costs` at the opening wages, the market rate and the opening's rent
stand-in; no price table, no demand, no income. The economy's markets then move prices off these.
"""
from sim.economy import api as economy_api
from sim.labour import api as labour_api
from sim.prices.api import long_run_costs


def wage_function(sim):
    """Money an hour of each trade pays at the opening: the labour market's quote, or for a trade it has not
    met (a plant's builders) the unskilled hour plus the trade's training premium, the rule the economy prices
    a trade with no wage by (sim/economy/trade_wages.py)."""
    registry = sim.state.trade_registry
    training_years_of = labour_api.wage_provider.training_years_by_trade(registry)
    unskilled = sim.economy.labour.quote(labour_api.trade_of_role(registry, "unskilled"))

    def wage_of(trade):
        quote = sim.economy.labour.quote(trade) if trade in registry else None
        if quote is not None and quote > 0.0:
            return quote
        training_years = training_years_of.get(trade, 0.0)    # a trade outside the registry has no training to price
        return unskilled * (1.0 + economy_api.premium_for_training_years(training_years))
    return wage_of


def cost_entries(sim):
    """The production entries the cost table is solved over."""
    return sim.production_catalog()


def opening_costs(sim, production=None):
    """{good: money per unit} the cost of making each good the society can make with the techniques it holds,
    at the opening wages, rate and rent. `production` replaces the shared entries (a crop made at its tiles' yield)."""
    production = cost_entries(sim) if production is None else production
    techniques = sim.production.techniques_granted() | frozenset(sim.production.techniques_in_use())
    wage_of = wage_function(sim)
    rent_of = long_run_costs.opening_rent_of(techniques, wage_of, sim.scenario.civ, production,
                                             registry=sim.state.trade_registry)
    costs = long_run_costs.long_run_costs(techniques, wage_of, float(sim.finance.market_rate()), rent_of, sim.scenario.civ,
                                          production, registry=sim.state.trade_registry)
    # A household good only a technique not yet held makes has no supplier at the opening, so it is seeded no
    # price that would draw demand to it; a founder's research or a partner's price brings it in.
    return {good: cost.cost for good, cost in costs.items()
            if cost.cost > 0.0 and not (cost.provenance == "gated" and sim.materials.serves_a_need(good))}
