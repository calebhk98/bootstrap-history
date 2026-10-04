"""The only door into sim/labour/: what code outside the package may import.

Outside code imports from here and reaches the simulation's labour through `sim.labour`
(a `Labour`, built by sim/engine/labour_port.py), never through a submodule or a private name.

`Labour` loads on first use (module `__getattr__`): the engine data modules import this door
for the wage constants while they are themselves still loading, and the labour mixins would
import them back.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine hands it what it needs (sim/engine/labour_port.py)

from . import wage_provider, wages
from .market.clearing import clear_all as clear_labour_markets
from .market.opening import opening_state as opening_labour_market
from .market.records import (Bid, Clearing, MarketState, Route, School, TradeSpec, YearInputs, YearReport,
                             from_plain as market_state_from_plain, people_in, to_plain as market_state_to_plain)
from .market.trades import fallback_trade, trade_specs
from .market.year import run_year as run_labour_year
from .labour_market import production_data
from .wage_provider import people_fed_per_worker
from .wages import CAREER_YEARS, HOURS_PER_WORKER_YEAR

__all__ = [
    "wage_provider", "wages", "Labour", "production_data",
    "people_fed_per_worker", "CAREER_YEARS", "HOURS_PER_WORKER_YEAR",
    # the labour-market core (sim/labour/market/DESIGN.md): plain records in, plain records out
    "run_labour_year", "clear_labour_markets", "opening_labour_market", "trade_specs", "fallback_trade", "people_in",
    "Bid", "Clearing", "MarketState", "Route", "School", "TradeSpec", "YearInputs", "YearReport",
    "market_state_to_plain", "market_state_from_plain",
]


def __getattr__(name):
    if name == "Labour":
        from .labour import Labour
        return Labour
    raise AttributeError(name)
