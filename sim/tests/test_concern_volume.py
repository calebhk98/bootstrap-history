"""Complaints 369, 370, 375: household income follows the wage and output per head. The wage rules are called with
figures built here. The chain from a cheaper entry to the concern's volume and takings, the market buying from the
cheaper producer, and a good offered after the opening becoming demand are in test_concern_volume_scenario; the volume,
takings and real-income rules are in test_concern_volume_rules, the copying time in test_technique_spread."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

import copy
from types import SimpleNamespace

from sim.engine.market_demand import MEAN_INCOME_HOURS_PER_CAPITA, MarketDemandMixin
from sim.labour.labour_market_api import LabourMarket


def wage_market(wage_index, wage_index_base, output_per_head, pay_share):
    market = LabourMarket.__new__(LabourMarket)
    market._world = SimpleNamespace(wage_index=wage_index, wage_index_base=wage_index_base,
                                    real_output_per_head=lambda: output_per_head)
    market._labour = SimpleNamespace(LABOUR_PAY_SHARE_OF_OUTPUT_GAIN=pay_share)
    return market


check("an hour pays the opening's when hands are as scarce as at the opening and output has not moved",
      wage_market(1.0, 1.0, 1.0, 1.0).household_wage_ratio() == 1.0)
check("a wage index that rises with the scarcity of hands raises the pay of an hour in proportion",
      abs(wage_market(1.3, 1.0, 1.0, 0.0).household_wage_ratio() - 1.3) < 1e-12)
check("pay follows output per head by the share it passes on",
      abs(wage_market(1.0, 1.0, 1.44, 0.5).household_wage_ratio() - 1.2) < 1e-12
      and wage_market(1.0, 1.0, 1.44, 0.0).household_wage_ratio() == 1.0)
check("the scarcity is read against the opening's index, not against one",
      abs(wage_market(1.2, 1.2, 1.0, 0.0).household_wage_ratio() - 1.0) < 1e-12)


class IncomeFromWage(MarketDemandMixin):
    def __init__(self, ratio):
        self.labour = SimpleNamespace(market=SimpleNamespace(household_wage_ratio=lambda: ratio))


check("household income is the mean income carried by what an hour pays now against the opening",
      abs(IncomeFromWage(1.25).household_income_hours_per_capita() - 1.25 * MEAN_INCOME_HOURS_PER_CAPITA) < 1e-9
      and IncomeFromWage(1.0).household_income_hours_per_capita() == MEAN_INCOME_HOURS_PER_CAPITA)
