"""Reporting's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, QUOTE, TABLE, ModuleSpec, PhaseHook, ViewSpec

from .commands import (CloseRealOutput, DiscardEventsAfter, ErodeMoney, RecordAutomation, RecordAutomationSkip,
                       RecordEvent)
from .log import AUDIT, LOG
from .module import Reporting
from .output import INDICATORS
from .state import ReportingSeat, ReportingWorld

# not cached: they read the agent economy's prices, which legacy code still writes
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "reporting", Reporting, channels=(LOG, AUDIT, INDICATORS), world_state=ReportingWorld, seat_state=ReportingSeat,
    publishes=(
        # cached: every write to the log and the indicators is a command or phase of this module
        ViewSpec("event_log", "event_log", kind=TABLE, channels=(LOG,), seat_scoped=True),
        ViewSpec("automation_rows", "automation_rows", kind=QUOTE, seat_scoped=True),
        ViewSpec("real_output_per_head", "real_output_per_head", kind=TABLE, channels=(INDICATORS,)),
        ViewSpec("money_real", "money_real", kind=TABLE, channels=(INDICATORS,)),
        ViewSpec("last_market_price_ratio", "last_market_price_ratio", kind=KEYED, channels=(INDICATORS,)),
        ViewSpec("real_output_hours", "real_output_hours", kind=QUOTE, **_LIVE),
        ViewSpec("real_price_ratio", "real_price_ratio", kind=KEYED, **_LIVE),
        ViewSpec("coin_value_ratio", "coin_value_ratio", kind=KEYED, **_LIVE),
    ),
    applies=((RecordEvent, "record_event"), (DiscardEventsAfter, "discard_events_after"),
             (RecordAutomation, "record_automation"), (RecordAutomationSkip, "record_automation_skip"),
             (CloseRealOutput, "close_real_output"), (ErodeMoney, "erode_money")),
    reads=("year", "acting_balance", "agent_prices", "agent_opening_basket", "agent_volume_baseline",
           "agent_traded_volumes", "new_goods_units", "household_prices", "money_per_labour_hour", "population_total",
           "opening_population", "home_coin_metal", "wage_materials"),
    phases=(PhaseHook("trim_audit", "trim_audit"), PhaseHook("wage_market_ratios", "record_wage_market_ratios")),
),)
