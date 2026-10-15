"""What the agent economy's opening is seeded with: the cost of making every good, nothing else.

Part of the port. `long_run_costs.long_run_costs` at the opening wages, the market rate and the opening's rent
stand-in; no price table, no demand, no income. The economy's markets then move prices off these.
"""
from . import long_run_costs
from .prices import default_production_entries, solver_wage_ratios


def wage_function(sim, production):
    """Money an hour of each trade pays at the opening: the labour market's quote, or for a trade it has not
    met (a plant's builders) the training rule's ratio to the unskilled hour."""
    from .data import TRADE_REGISTRY
    numeraire_trade = long_run_costs.solve_prices.NUMERAIRE_TRADE
    unskilled = sim.economy.labour.quote(numeraire_trade)
    ratios = solver_wage_ratios(production, {})

    def wage_of(trade):
        quote = sim.economy.labour.quote(trade) if trade in TRADE_REGISTRY else 0.0
        return quote if quote > 0.0 else unskilled * ratios.get(trade, 1.0)
    return wage_of


def opening_costs(sim):
    """{good: money per unit} the cost of making each good the society can make with the techniques it holds,
    at the opening wages, rate and rent."""
    production = default_production_entries()
    techniques = frozenset(sim.state.projects.granted) | frozenset(sim.techniques_in_use())
    wage_of = wage_function(sim, production)
    rent_of = long_run_costs.opening_rent_of(techniques, wage_of, sim.civ, production)
    costs = long_run_costs.long_run_costs(techniques, wage_of, float(sim.economy.base_rate()), rent_of, sim.civ,
                                          production)
    return {good: cost.cost for good, cost in costs.items() if cost.cost > 0.0}
