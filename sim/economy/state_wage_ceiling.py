"""The ceiling the state and its mints bid labour up to, a multiple of the going wage; a leaf both import."""
from sim.constants import declare

STATE_WAGE_CEILING_MULTIPLE = declare(
    "STATE_WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic",
    unit="multiple of last year's wage the state will bid",
    source=None, confidence="D",
    why="How far above last year's wage the state is willing to go to fill its posts; the labour market "
        "moves the wage only part of the way anyway.")
