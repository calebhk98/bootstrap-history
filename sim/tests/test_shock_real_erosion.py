"""The hazards module's real_erosion_seats: a debasement multiplies the coin's purchasing power by what it leaves, each holder is
told in a log line of kind hazard_coin_debased naming the hazard, and the telling is not repeated within the cooling-off years."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.hazards import constants
from sim.hazards.state import HazardsWorld
from sim.ledger.api import PayEdge
from sim.reporting.api import ErodeMoney, RecordEvent, ReportingWorld
from sim.reporting.module import Reporting
from sim.tests import hazards_host, module_harness

HAZARD = {"name": "debasement", "real_erosion": 0.2}


class StandIn:
    """The module over a purse and the reporting module: an ErodeMoney it sends moves the coin's value, a PayEdge empties the purse."""

    def __init__(self, capital=0.0):
        self.household = SimpleNamespace(capital=capital)
        self.reporting = module_harness.build(Reporting, world=ReportingWorld())

        def pay_edge(command):
            self.household.capital -= command.amount

        self.module = hazards_host.build(
            world=HazardsWorld(said_debasement=0), acting_balance=lambda: self.household.capital,
            money_real=lambda: self.reporting.money_real(),
            answers={ErodeMoney: lambda command: self.reporting.erode_money(command), PayEdge: pay_edge})

    @property
    def money_real(self):
        return self.reporting.money_real()

    def erode(self, met, year):
        self.module.real_erosion_seats(met, year)

    def lines(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]


world = StandIn()
world.erode({"seat": HAZARD}, 210)
check("the coin keeps what the debasement leaves of its purchasing power", abs(world.money_real - 0.8) < 1e-12,
      world.money_real)
line = world.lines()[0]
check("the holder is told with a line of kind hazard_coin_debased naming the hazard",
      (line.kind, line.facts["hazard"]) == ("hazard_coin_debased", "debasement"), line)
world.erode({"seat": HAZARD}, 214)
check("a second debasement within the cooling-off years bites but is not told again",
      abs(world.money_real - 0.64) < 1e-12 and len(world.lines()) == 1, (world.money_real, world.lines()))
world.erode({"seat": HAZARD}, 230)
check("after the cooling-off years it is told again", len(world.lines()) == 2, world.lines())

holding = StandIn(capital=100.0)
holding.erode({"seat": HAZARD}, 210)
check("cash held bites by the erosion times the cash-loss share",
      abs(holding.household.capital - (100.0 - 100.0 * 0.2 * constants.REAL_EROSION_CASH_LOSS_SHARE)) < 1e-9, holding.household.capital)

untouched = StandIn()
untouched.erode({"seat": {"name": "plague", "staff_loss": 0.1}}, 210)
check("a hazard with no real erosion leaves the coin alone", untouched.money_real == 1.0 and untouched.lines() == [])
