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
from .market.migration import move_shares as migration_shares
from .regional_migration import moves_between_regions
from .market.records import (Bid, Clearing, MarketState, Route, School, TradeSpec, YearInputs, YearReport,
                             copy_state as copy_market_state, from_plain as market_state_from_plain, people_in, to_plain as market_state_to_plain)
from .market.trades import fallback_trade, trade_specs
from .market.year import run_year as run_labour_year
from .labour_market import production_data
from .food_gathering import cap_share, capped_kcal, hours_cap_kcal
from .wage_provider import people_fed_per_worker
from .wages import CAREER_YEARS
from .trade_data import tool_draw, tool_hours_factors, tool_order
from .occupational_shares import occupational_report, shares_by_group, hours_by_trade_of_all_employers, format_report as format_occupational_report, groups_data as occupation_groups
from .town_providers import register_town_premium, register_town_provider
from .staff_targets import scholar_target
from .tenure import add_tenure, fade_tenure, outflow_shares, tenure_by_trade, tenure_held

__all__ = [
    "occupational_report", "shares_by_group", "hours_by_trade_of_all_employers", "format_occupational_report", "occupation_groups",
    "wage_provider", "wages", "scholar_target", "Labour", "register_town_provider", "register_town_premium", "production_data",
    "people_fed_per_worker", "CAREER_YEARS", "tool_draw", "tool_hours_factors", "tool_order",
    "add_tenure", "fade_tenure", "outflow_shares", "tenure_by_trade", "tenure_held", "hours_cap_kcal", "capped_kcal", "cap_share",
    # the labour-market core (sim/labour/market/DESIGN.md): plain records in, plain records out
    "run_labour_year", "migration_shares", "moves_between_regions", "clear_labour_markets", "opening_labour_market", "trade_specs", "fallback_trade", "people_in",
    "Bid", "Clearing", "MarketState", "Route", "School", "TradeSpec", "YearInputs", "YearReport",
    "market_state_to_plain", "market_state_from_plain", "copy_market_state",
]


def __getattr__(name):
    if name == "Labour":
        from .labour import Labour
        return Labour
    raise AttributeError(name)
