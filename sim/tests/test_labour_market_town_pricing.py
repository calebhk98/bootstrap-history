"""Complaint 368: the housing term of a wage comes from the town the work is in, not from one household, and
commission pay takes the quoted hour; hiring leans on a trade's price and letting people go eases it. Complaint 640:
the rules are called on a stub labour and world built here; the whole-game checks are in
test_labour_market_town_pricing_scenario."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403

from sim.agents.base import RecordedActor
from sim.engine.state import ActorRecord
from sim.labour.labour_market_api import LabourMarket
from sim.labour.labour_wages import WagesMixin

TRADE = "artisan"
HOURS = 2000.0
TOWN_PEOPLE = 20000.0


class _Market(LabourMarket):
    def standing_draw(self, trade):
        return 0.0


def _market(founder_staff=0.0, firm_staff=0.0, housing_built=0.0, supply=500.0, wage_per_hour=2.0):
    """A market over a stub labour and world: a town of TOWN_PEOPLE, the founder's staff and firms' staff on its books."""
    household = types.SimpleNamespace(worker_housing_places=housing_built, labour_pressure_records={})
    world = types.SimpleNamespace(
        state=types.SimpleNamespace(household=household, scenario=types.SimpleNamespace(year=100)),
        HOURS_PER_PERSON_YEAR=HOURS, actor_staff_total=lambda: firm_staff,
        economy=types.SimpleNamespace(agent_wage_per_hour=lambda trade: wage_per_hour))
    labour = types.SimpleNamespace(
        _world=world, headcount=lambda: founder_staff, home_town_population_estimate=lambda: TOWN_PEOPLE,
        market_supply=lambda trade: supply, HOUSING_PRESSURE_START_OCCUPANCY=WagesMixin.HOUSING_PRESSURE_START_OCCUPANCY,
        HOUSING_PRESSURE_BAND=WagesMixin.HOUSING_PRESSURE_BAND, HOUSING_PRESSURE_MAX_MARKUP=WagesMixin.HOUSING_PRESSURE_MAX_MARKUP)
    return _Market(labour)


_room = _market().town_housing_room()
_full = _room * 1.2

# ---- housing is a fact about the town, whoever employs the people
_by_founder = _market(founder_staff=_full).town_housing_factor()
check("a crowded town raises the housing factor", _by_founder > 1.0 + 1e-9, _by_founder)
check("the same people on a firm's books give the same housing factor as on the founder's",
      abs(_market(firm_staff=_full).town_housing_factor() - _by_founder) < 1e-12)
check("the housing factor does not depend on how the people are split between employers",
      abs(_market(founder_staff=_full / 2, firm_staff=_full / 2).town_housing_factor() - _by_founder) < 1e-12)
check("an empty town has no housing premium", _market().town_housing_factor() == 1.0)
check("housing built in the town eases the factor for everyone",
      _market(founder_staff=_full, housing_built=_full).town_housing_factor() < _by_founder)
check("the housing premium never exceeds its declared maximum",
      _market(founder_staff=100.0 * _full).town_housing_factor() <= 1.0 + WagesMixin.HOUSING_PRESSURE_MAX_MARKUP + 1e-12)
check("the housing room is the spare share of the town's dwellings plus what was built",
      abs(_market(housing_built=50.0).town_housing_room() - _room - 50.0) < 1e-9)

# ---- the quote does not depend on who asks
_quote_market = _market(founder_staff=_full)
check("a firm and the founder hiring the same trade are quoted the same hour",
      _quote_market.quote(TRADE, 0.0, employer="a firm") == _quote_market.quote(TRADE, 0.0, employer="the founder"))
check("an hour is the person-year over the hours in a person's year",
      abs(_quote_market.quote(TRADE) * HOURS - _quote_market.quote_annual(TRADE)) < 1e-9)
check("a pay premium raises the quote by that fraction", abs(_quote_market.quote(TRADE, pay_premium=0.25) / _quote_market.quote(TRADE) - 1.25) < 1e-12)

# ---- commission pays the quoted hour times the shop's premium
check("a commissioned hour is the market's quoted hour times the shop's premium",
      abs(_quote_market.commission_cost(TRADE, 100.0, 1.7) - 100.0 * 1.7 * _quote_market.quote(TRADE)) < 1e-9)

# ---- leaning on a trade raises its price; letting people go eases it
_leaned = _market(supply=1000.0)
_before = _leaned.quote(TRADE)
_leaned.hire("employer", TRADE, 500.0)
check("hiring leans on the trade and raises its quote", _leaned.pressure(TRADE) == 500.0 and _leaned.quote(TRADE) > _before)
_pressed = _leaned.pressure(TRADE)
_leaned.release("employer", TRADE, 300.0)
check("releasing hours eases the pressure by exactly those hours", abs(_leaned.pressure(TRADE) - (_pressed - 300.0)) < 1e-9, _leaned.pressure(TRADE))
_leaned.release("employer", TRADE, 5000.0)
check("releasing more than was leaned on takes the pressure to zero, not below", _leaned.pressure(TRADE) == 0.0)
_never = _market()
_never.release("employer", TRADE, 100.0)
check("releasing a trade nobody leaned on changes nothing", _never.pressure(TRADE) == 0.0)


# ---- the forecast of hiring one more is the price factor once they are on the books
class _GrowingSupply(_Market):
    """A market whose supply grows with the people the household employs of the trade."""

    def __init__(self, base_supply):
        super().__init__(_market().__dict__["_labour"])
        self._employed = {}
        labour = self._labour
        labour.employed = lambda trade: self._employed.get(trade, 0.0)
        labour.set_employed = lambda trade, people: self._employed.__setitem__(trade, people)
        labour.market_supply = lambda trade: base_supply + self._employed.get(trade, 0.0) * HOURS


_scarce = _GrowingSupply(base_supply=3.0 * HOURS)
_forecast = _scarce.price_factor_after(TRADE, 1.0)
check("a scarce trade's forecast for hiring one is dearer than the factor as it stands", _forecast > _scarce.price_factor(TRADE), _forecast)
_scarce._employed[TRADE] = 1.0
_scarce.press(TRADE, HOURS)
check("the forecast is the factor once the hire is really on the books", abs(_scarce.price_factor(TRADE) - _forecast) < 1e-12,
      (_scarce.price_factor(TRADE), _forecast))
_deep = _GrowingSupply(base_supply=1.0e6 * HOURS)
check("an abundant trade is hardly moved by one hire", _deep.price_factor_after(TRADE, 1.0) - _deep.price_factor(TRADE) < 1e-9)
check("the forecast of no people is the factor as it stands", _deep.price_factor_after(TRADE, 0.0) == _deep.price_factor(TRADE))
check("the pressure factor is capped however hard a trade is leaned on",
      abs(_scarce._price_factor_from(1.0e12, 1.0) - (1.0 + _scarce.LABOUR_PRICE_PRESSURE_COEFFICIENT * _scarce.LABOUR_PRESSURE_SHARE_CAP ** 2)) < 1e-12)


# ---- a firm's staff changes reach the market
class _RecordingMarket:
    def __init__(self):
        self.calls = []

    def hire(self, employer, trade, hours, pay_premium=0.0):
        self.calls.append(("hire", trade, hours))

    def release(self, employer, trade, hours):
        self.calls.append(("release", trade, hours))


def _firm(workforce):
    return RecordedActor("firm:test", ActorRecord(kind="firm", money=1.0e6, workforce=dict(workforce)))


_market_log = _RecordingMarket()
_world = types.SimpleNamespace(labour_market=_market_log, hours_per_person_year=HOURS)
_firm({TRADE: 4.0, "mason": 1.0}).press_new_staff({TRADE: 1.0, "mason": 1.0}, _world)
check("a firm taking people on presses the market by their hours", _market_log.calls == [("hire", TRADE, 3.0 * HOURS)], _market_log.calls)
_market_log.calls.clear()
_firm({TRADE: 1.0}).press_new_staff({TRADE: 4.0, "scribe": 2.0}, _world)
check("a firm shedding staff eases the pressure for every trade it let go of",
      _market_log.calls == [("release", TRADE, 3.0 * HOURS), ("release", "scribe", 2.0 * HOURS)], _market_log.calls)
_market_log.calls.clear()
_firm({TRADE: 2.0}).press_new_staff({TRADE: 2.0}, _world)
check("a firm whose staff did not change does not touch the market", _market_log.calls == [])
