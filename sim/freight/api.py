"""The freight package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import PayRouteDues
from .constants import FREIGHT_DRIVER_WAGE_TRADE, FREIGHT_FEED_PRICE_MATERIAL, SEA_MODE
from .route import Leg, Route
from . import rules
