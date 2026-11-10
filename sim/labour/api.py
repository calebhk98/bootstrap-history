"""The only door into sim/labour/: what code outside the package may import.

Outside code imports from here and asks the workforce module's views for the simulation's labour (a `Labour`, held by
the module, sim/workforce/module.py), never through a submodule or a private name.

`Labour` loads on first use (module `__getattr__`): the engine data modules import this door
for the wage constants while they are themselves still loading, and the labour parts would
import them back.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the workforce module hands it what it needs (sim/workforce/world.py)

from . import learning_curve, wage_provider, wages
from .trade_formation import SOURCE_TASK_FLOOR_FRACTION
from .market.reservation import reservation_wage_per_hour
from .market.opening import opening_state as opening_labour_market
from .market.migration import move_shares as migration_shares
from .regional_migration import migrant_pairs, totals_of_pairs
from .market.records import (EmployerHoursBid, LabourClearing, MarketState, Route, School, TradeSpec, YearInputs, YearReport,
                             from_plain as market_state_from_plain, people_in, to_plain as market_state_to_plain)
from .market.bid_book import TrancheBids
from .market.bid_table import LabourBidTable, RowBlocks, RowNames
from .market.state_reads import (grid_rows_of, hours_cleared_at, people_at, people_by_trade_in_each_area, people_by_trade_over, people_in_areas, people_weighted_wage_by_area,
                                 scale_people_in_area, scale_people_in_areas, wage_means_by_group, wages_in_view_order, working_people_in_areas)
from .market.exact_sums import python_sum
from .market.trades import fallback_trade, trade_specs
from .trade_seed import bound_by_hirers, seed_hours
from .market.year import run_year as run_labour_year
from .market.fetch_wage import fetch_wage
from .market.sold_hours_kernel import (OFFER_HAS_PLOT, OFFER_HOURS, OFFER_MARGINAL, OFFER_PER_WORKER, OFFER_PLAN, OFFER_ROWS,
                                       OFFER_SHARE, OFFER_USABLE, OFFER_WHOLE, OFFER_WORK, OFFER_WORKERS, hours_kept_at_home,
                                       plot_hours_at_wage, sold_hours, sold_hours_range)
from .market.fetch_wage_samples import samples as fetch_wage_samples
from .food_gathering import cap_share, capped_kcal, hours_cap_kcal
from .wage_provider import people_fed_per_worker
from .wages import CAREER_YEARS
from .trade_data import (bonded_pseudo_trade, craft_family, farm_trade, generic_craft_trade, generic_staff_trades, role_field, scholar_trade,
                         staff_resource_trade, trade_of_role, tool_draw, tool_hours_factors, tool_order)
from .occupational_shares import occupational_report, shares_by_group, hours_by_trade, hours_by_trade_of_all_employers, people_by_trade_of_all_employers, format_report as format_occupational_report, groups_data as occupation_groups
from .staff_targets import scholar_target
from .school_seats import schools_of_actor
from .staff_moves import stochastic_round
from .labour_state_weights import STATE_WEIGHTS
from .people_added import add_people
from .tenure import add_tenure, fade_tenure, outflow_shares, tenure_by_trade, tenure_held

__all__ = [
    "learning_curve", "SOURCE_TASK_FLOOR_FRACTION",
    "fetch_wage", "fetch_wage_samples",
    "sold_hours", "sold_hours_range", "plot_hours_at_wage", "hours_kept_at_home", "OFFER_ROWS", "OFFER_HOURS", "OFFER_WHOLE", "OFFER_SHARE", "OFFER_PLAN", "OFFER_WORK", "OFFER_HAS_PLOT", "OFFER_PER_WORKER",
    "OFFER_MARGINAL", "OFFER_USABLE", "OFFER_WORKERS",
    "occupational_report", "shares_by_group", "hours_by_trade", "hours_by_trade_of_all_employers", "people_by_trade_of_all_employers", "format_occupational_report", "occupation_groups",
    "wage_provider", "wages", "scholar_target", "stochastic_round", "STATE_WEIGHTS", "add_people", "Labour",
    "people_fed_per_worker", "CAREER_YEARS", "tool_draw", "tool_hours_factors", "tool_order",
    "add_tenure", "fade_tenure", "outflow_shares", "tenure_by_trade", "tenure_held", "hours_cap_kcal", "capped_kcal", "cap_share",
    # the labour-market core (sim/labour/market/DESIGN.md): plain records in, plain records out
    "run_labour_year", "reservation_wage_per_hour", "migration_shares", "migrant_pairs", "totals_of_pairs", "opening_labour_market", "seed_hours", "bound_by_hirers", "trade_specs", "fallback_trade", "role_field", "trade_of_role", "generic_craft_trade", "bonded_pseudo_trade", "scholar_trade", "craft_family", "farm_trade", "generic_staff_trades", "staff_resource_trade", "people_in",
    "grid_rows_of", "hours_cleared_at", "people_at", "people_by_trade_in_each_area", "people_by_trade_over", "people_in_areas", "people_weighted_wage_by_area", "scale_people_in_area", "scale_people_in_areas",
    "wage_means_by_group", "wages_in_view_order", "working_people_in_areas",
    "schools_of_actor", "EmployerHoursBid", "TrancheBids", "LabourBidTable", "RowBlocks", "RowNames", "python_sum", "LabourClearing", "MarketState", "Route", "School", "TradeSpec", "YearInputs", "YearReport",
    "market_state_to_plain", "market_state_from_plain",
]


def __getattr__(name):
    if name == "Labour":
        from .labour import Labour
        return Labour
    raise AttributeError(name)
