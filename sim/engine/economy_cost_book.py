"""The prices, wages, rate and rent the economy shows now, as the functions the cost calculator takes.

A producer judging what a good costs it to make asks the economy: the price of each input where the home
sellers have a market (the long-run cost of making where they have none), the wage of each trade, the lending
rate and the rent land lets at. Ore carries no rent here: the mine's own cost is the recipe that digs it.
"""
from .entry_cost import CostBook
from .making_cost import LAND_MATERIAL


def economy_cost_book(sim, production=None) -> CostBook:
    """A `CostBook` at the economy's prices, wages, lending rate and land rent as they stand."""
    prices = sim.goods_market.household_prices()
    economy = sim.economy
    land_rent = economy.agent_land_rent_per_hectare() or 0.0
    wages = {}

    def input_price_of(material):
        if material == LAND_MATERIAL:
            return None     # land is charged its rent (rent_of), not a price in the table
        price = prices.get(material)
        return price if price is not None and price > 0.0 else None

    def wage_of(trade):
        if trade not in wages:
            wage = economy.agent_wage_per_hour(trade)
            wages[trade] = wage if wage else sim.labour.market.quote(trade)
        return wages[trade]

    def rent_of(key):
        return land_rent if key == LAND_MATERIAL else 0.0

    return CostBook(input_price_of, wage_of, float(sim.market_rate()), rent_of=rent_of,
                    civilization=sim.civ, production=production)
