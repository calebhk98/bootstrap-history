"""A small hand-made household basket, for tests of the Stone-Geary arithmetic only.

The simulation itself derives demand from needs (sim/world/need_demand.py);
these goods exist so the demand-system maths can be checked on fixed shares.
"""
from sim.world import demand

FOOD = demand.Good(
    "wheat_kg", demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR, 0.30)
MANUFACTURES = demand.Good("manufactures", 0.0, 0.64)
SILVER = demand.Good("silver_kg", 0.0, 0.05)
PLATINUM = demand.Good("platinum_g", 0.0, 0.01)
BASKET = (FOOD, MANUFACTURES, SILVER, PLATINUM)
demand.validate_basket(BASKET)
