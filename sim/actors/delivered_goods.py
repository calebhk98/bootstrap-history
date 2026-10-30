"""Goods the market delivers into an actor's stores; kept apart from the engine's year of the economy, which never reads an actor's record."""
from sim.agents.api import stock_keeping
from sim.world.material_units import tonnes_per_unit


def keep_deliveries(known, delivered):
    """Goods each buyer that keeps its purchases bought at the market join its stores, in tonnes."""
    for buyer in sorted(delivered):
        if getattr(known[buyer], "keeps_purchases", False):
            stock_keeping.add_delivery(known[buyer].record.stores, {
                good: units * tonnes_per_unit(good) for good, units in delivered[buyer].items()})
