"""What a coin is worth at the opening: the cost of making its metal at the margin.

Part of the port. The coin standard fixes how much metal a unit of money holds, so a unit is worth that metal.
The metal the money loses each year is made by the recipes the opening runs for it, the cheapest first up to
what deposits and joint products allow; the last of them sets what the metal costs to make in the quantity the
money needs, and that is what the metal is worth. If it costs more than the table's cost of the cheapest way
(a by-product route that cannot supply the quantity), an hour of work is worth fewer coins and every other price
and wage is lower in coin by the same share; the metal's price in coin is fixed by the standard and stays.
"""
from sim.economy import api as economy_api

from .economy_port_setup import build_setup


def priced_at_the_margin(sim, opening):
    """`opening` with its coin figures counted at the coin the metal's marginal cost makes: the share the
    prices, wages and carriage are scaled by is kept as `coin_worth_scale` (1 when the money has no metal)."""
    found = economy_api.backing_marginal_cost(economy_api.blank_economy(build_setup(sim, opening)))
    if found is None:
        return dict(opening, coin_worth_scale=1.0)
    marginal, price = found
    scale = price / marginal
    metal = sim.civ["coin_standard"].get("material")
    scaled = dict(opening)
    scaled["prices"] = {good: (value if good == metal else value * scale) for good, value in opening["prices"].items()}
    scaled["wages"] = {trade: value * scale for trade, value in opening["wages"].items()}
    scaled["carriage"] = {mode: value * scale for mode, value in opening["carriage"].items()}
    scaled["carriage_balanced"] = {mode: value * scale for mode, value in opening["carriage_balanced"].items()}
    scaled["coin_worth_scale"] = scale
    return scaled
