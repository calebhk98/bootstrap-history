"""Declared numbers the demography module owns."""
from sim.constants import declare

DEFAULT_POPULATION_100AD = declare(
    "DEFAULT_POPULATION_100AD", 65e6, kind="initial_condition",
    unit="people", source="Widely cited estimate of the Roman Empire's "
         "population around 100 AD.",
    confidence="C",
    why="Fallback starting population, and the reference population "
        "pop_scale=1.0 is defined against, for a civilisation file "
        "that does not set its own `population` field. Every shipped "
        "civ file does set one; this is the scenario's own initial "
        "condition, not a tuned game-balance number.")

POP_SCALE_FLOOR = declare(
    "POP_SCALE_FLOOR", 0.05, kind="temporary_heuristic",
    unit="dimensionless (minimum pop_scale)", source=None,
    confidence="D",
    why="Floor under pop_scale so a tiny starting civilisation "
        "population never divides a formula by something vanishingly "
        "small. Guard value, not a demographic claim.")

YEARLY_RECORD_LIMIT = 300   # years of the demographic record kept
URBAN_SHARE_BAND_KEYS = ("low", "high", "threshold", "source", "confidence")
