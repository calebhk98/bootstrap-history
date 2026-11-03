"""Complaint 103: a trade nobody here practises, taught by the founder, has a pool too. A firm staffs from the people
the founder taught who are not on the founder's payroll or another actor's, so it cannot run on staff that do not exist."""

QUICK_TOPIC = True

import types

from .harness import check

from sim.agents import business_crew
from sim.agents.business import Business
from sim.actors.world import ActorWorld
from sim.engine.data import TRADES_ABSENT
from sim.tests.world_stand_in import fake_needs

TAUGHT = sorted(TRADES_ABSENT)[0]


class Labour:
    taught = 12.0
    available = True

    def trade_available(self, trade):
        return self.available

    def people_who_exist(self, trade):
        return 1000.0

    def taught_trade_people(self, trade):
        return self.taught


def make_world(taught=12.0, founder_staff=2.0, actor_staff=3.0):
    labour = Labour()
    labour.taught = taught
    actors = types.SimpleNamespace(home_staff_fte=lambda trade, excluding=None: actor_staff if trade == TAUGHT else 0.0)
    needs = fake_needs(trade_available=labour.trade_available, people_who_exist=labour.people_who_exist,
                       taught_trade_people=labour.taught_trade_people, trades_absent=TRADES_ABSENT,
                       staff_on_all_books=lambda trade: {TAUGHT: founder_staff, "smith": 5.0}.get(trade, 0.0))
    world = ActorWorld(needs, types.SimpleNamespace(cast=lambda: actors))
    world.fixture = labour   # the facts the stand-in game answers, kept to change them
    return world


check("the trade the founder teaches is one nobody here practises", TAUGHT in TRADES_ABSENT, TAUGHT)
check("the pool is what the founder taught, less the founder's staff and the other actors'",
      make_world().labour.free_fte(TAUGHT, "firm:1") == 12.0 - 2.0 - 3.0)
check("a taught trade has a pool", make_world().labour.free_fte(TAUGHT, "firm:1") is not None)
world = make_world()
world.fixture.available = False
check("a trade that is not available stays without a pool", world.labour.free_fte(TAUGHT, "firm:1") is None)
check("when the founder and others hold all of it, none is free", make_world(taught=4.0).labour.free_fte(TAUGHT, "firm:1") == 0.0)
check("a trade people practise already is drawn from the whole country's people", make_world().labour.free_fte("smith", "firm:1") == 1000.0 - 5.0 - 0.0)


class Firm:
    actor_id = "firm:1"

    def __init__(self, hired=0.0):
        self.workforce = {TAUGHT: hired} if hired else {}
        self.record = types.SimpleNamespace(staff_wanted={})
        self.holdings = types.SimpleNamespace(capacity_of=lambda node_id: 1.0)


class StaffWorld:
    def concern_staff(self, node_id):
        return {TAUGHT: 4.0}


firm = Firm()
check("a firm with none of the taught people hired finds none of its staff, and posts the places",
      business_crew.staff(Business(), firm, "mill", StaffWorld()) == 0.0 and firm.record.staff_wanted == {TAUGHT: 4.0}, firm.record.staff_wanted)
firm = Firm(hired=3.0)
check("a firm takes the share of its places the labour core has hired people for",
      business_crew.staff(Business(), firm, "mill", StaffWorld()) == 0.75 and firm.record.staff_wanted == {TAUGHT: 4.0})
