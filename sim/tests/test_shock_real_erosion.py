"""ShockYearMixin._shock_real_erosion_seats on a stand-in self: a debasement multiplies the coin's purchasing power by what it
leaves, each holder is told in a log line of kind hazard_coin_debased naming the hazard, and the telling is not repeated within
the cooling-off years."""
QUICK_TOPIC = True

import contextlib
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.shock_year import ShockYearMixin
from sim.refusal import cause_of, facts_of
from sim.tests import event_stand_in

HAZARD = {"name": "debasement", "real_erosion": 0.2}


class StandIn:
    send = event_stand_in.send
    REAL_EROSION_CASH_LOSS_SHARE = 0.5

    def __init__(self, capital=0.0):
        household = SimpleNamespace(capital=capital, log=[])
        self.state = SimpleNamespace(
            economy=SimpleNamespace(money_real=1.0), scenario=SimpleNamespace(_said_debasement=0, year=210), acting_seat="seat",
            seats={"seat": SimpleNamespace(household=household)}, household=household)
        self.household = household

    @contextlib.contextmanager
    def act_as(self, seat_id):
        yield

    def hazard_relief_detail(self, kind):
        return 1.0, [], []

    def lose_capital(self, share, why):
        self.household.capital *= 1.0 - share


world = StandIn()
ShockYearMixin._shock_real_erosion_seats(world, {"seat": HAZARD}, 210)
check("the coin keeps what the debasement leaves of its purchasing power", abs(world.state.economy.money_real - 0.8) < 1e-12,
      world.state.economy.money_real)
line = world.household.log[0][1]
check("the holder is told with a line of kind hazard_coin_debased naming the hazard",
      (cause_of(line), facts_of(line)["hazard"]) == ("hazard_coin_debased", "debasement"), line)
ShockYearMixin._shock_real_erosion_seats(world, {"seat": HAZARD}, 214)
check("a second debasement within the cooling-off years bites but is not told again",
      abs(world.state.economy.money_real - 0.64) < 1e-12 and len(world.household.log) == 1, (world.state.economy.money_real, world.household.log))
ShockYearMixin._shock_real_erosion_seats(world, {"seat": HAZARD}, 230)
check("after the cooling-off years it is told again", len(world.household.log) == 2, world.household.log)

holding = StandIn(capital=100.0)
ShockYearMixin._shock_real_erosion_seats(holding, {"seat": HAZARD}, 210)
check("cash held bites by the erosion times the cash-loss share", abs(holding.household.capital - 90.0) < 1e-9, holding.household.capital)

untouched = StandIn()
ShockYearMixin._shock_real_erosion_seats(untouched, {"seat": {"name": "plague", "staff_loss": 0.1}}, 210)
check("a hazard with no real erosion leaves the coin alone", untouched.state.economy.money_real == 1.0 and untouched.household.log == [])
