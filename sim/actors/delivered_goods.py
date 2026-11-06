"""Goods the market delivers into an actor's stores; kept apart from the engine's year of the economy, which never reads an actor's record."""
from sim.agents.api import stock_keeping


def keep_deliveries(known, delivered, tonnes_per_unit):
    """Goods each buyer that keeps its purchases bought at the market join its stores, in tonnes. `tonnes_per_unit(good)` is
    the economy's mass of a unit (the markets `unit_mass_kg` view), None for a good with no finite mass, which is not carried."""
    for buyer in sorted(delivered):
        if known[buyer].keeps_purchases:
            tonnes = {good: units * tonnes_per_unit(good) for good, units in sorted(delivered[buyer].items())
                      if tonnes_per_unit(good) is not None}
            stock_keeping.add_delivery(known[buyer].record.stores, tonnes)
