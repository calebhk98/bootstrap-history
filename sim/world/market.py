"""Two figures the price and merchant models still share; the year's market is the agent economy's (sim/economy)."""
from sim.constants import declare

DEFAULT_DEMAND_PRICE_ELASTICITY = declare(
    "DEFAULT_DEMAND_PRICE_ELASTICITY", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fall in quantity demanded per rise in price, in logs)",
    source=None, confidence="D",
    why="Short-run household and derived demand for a material is inelastic: "
        "recipes and habits do not change within a year. One value for every "
        "material; the need model's own substitution between goods "
        "(NEED_SUBSTITUTION_ELASTICITY) would give a per-material figure.")

UNSPLIT_FLOOR_RATIO = 1.0   # a producer whose cost has no running part to idle on sells at no less than its cost
