"""Pay over the market: a premium raises the quote, widens what an employer can recruit and draws its
hires from rivals rather than idle hands. Stub world, no Sim; invented trade ids."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.labour.labour_market_api import LabourMarket

HOURS = 2000.0
FALLBACK = "gleaner"
SOLDIERLY = "soldier"  # the id legacy_trade_defaults lists as drawn from the unskilled pool


class StubLabour:
    """Just what LabourMarket touches."""

    def __init__(self, world):
        self._world = world

    def market_supply(self, trade):
        return 1000.0 * HOURS

    def wage_schedule(self):
        return SimpleNamespace(training_years={FALLBACK: 0.0, "weaver": 3.0, SOLDIERLY: 0.5})

    def base_annual_wage(self, trade):
        return 100.0

    def wage_cost_factors(self, trade):
        return {"weighted": 1.0}


def stub_market():
    household = SimpleNamespace(labour_pressure_records={}, employees={})
    world = SimpleNamespace(
        state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=0)),
        HOURS_PER_PERSON_YEAR=HOURS, wages={FALLBACK: 1, "weaver": 1, SOLDIERLY: 1},
        trade_family=lambda trade: "craft", price_index=1.0, wage_index=1.0,
        actor_staff_fte=lambda trade: 10.0 if trade == SOLDIERLY else 0.0,
        economy=SimpleNamespace(agent_wage_per_hour=lambda trade: 0.05))
    return LabourMarket(StubLabour(world))


market = stub_market()
plain = market.quote("weaver", 0.0)
check("zero premium quotes the unpremiumed rate", market.quote("weaver", 0.0, None, 0.0) == plain)
check("a premium raises the quote proportionally", abs(market.quote("weaver", 0.0, None, 0.25) - plain * 1.25) < 1e-12)
check("the annual quote scales the same way",
      abs(market.quote_annual("weaver", 0.0, None, 0.5) - market.quote_annual("weaver") * 1.5) < 1e-9)

low = market.recruitable("weaver", 100.0)
check("a premium raises recruits", market.recruitable("weaver", 100.0, 0.3) > low)
check("asking for more people fills a smaller share", market.recruitable("weaver", 5000.0) / 5000.0 < low / 100.0)
check("recruits never exceed the people asked for", all(market.recruitable("weaver", count, premium) <= count
                                                         for count in (1.0, 100.0, 1e6) for premium in (0.0, 1.0, 9.0)))
check("asking for nobody finds nobody", market.recruitable("weaver", 0.0) == 0.0)

premium_market = stub_market()
hired_rate = premium_market.hire("firm", "weaver", 1000.0, pay_premium=0.5)
check("hire returns the premium-inclusive rate", abs(hired_rate - plain * 1.5) < 1e-9 * plain, (hired_rate, plain))
plain_market = stub_market()
check("a zero-premium hire records the full hours and returns the plain rate",
      plain_market.hire("firm", "weaver", 1000.0) == plain and plain_market.recent_pressure("weaver") == 1000.0)
check("a hire with a premium leaves less pressure",
      0.0 < premium_market.recent_pressure("weaver") < plain_market.recent_pressure("weaver"))

check("standing draw falls on the fallback trade only",
      market.standing_draw("weaver") == 0.0 and market.standing_draw(FALLBACK) == 10.0 * HOURS)
