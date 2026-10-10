"""Complaint 103: a trade nobody here practises, taught by the founder, has a pool too. A firm staffs from the people
the founder taught who are not on the founder's payroll or another actor's, so it cannot run on staff that do not exist."""

QUICK_TOPIC = True

import types

from .harness import check

from sim.agents import concern_ops
from sim.engine.agents_port import SimWorld
from sim.engine.data import TRADES_ABSENT

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
    seats = {"founder": types.SimpleNamespace(household=types.SimpleNamespace(employees={TAUGHT: founder_staff, "smith": 5.0}))}
    actors = types.SimpleNamespace(staff_fte=lambda trade, excluding=None: actor_staff if trade == TAUGHT else 0.0)
    return SimWorld(types.SimpleNamespace(labour=labour, state=types.SimpleNamespace(seats=seats), actors=actors))


check("the trade the founder teaches is one nobody here practises", TAUGHT in TRADES_ABSENT, TAUGHT)
check("the pool is what the founder taught, less the founder's staff and the other actors'",
      make_world().free_fte(TAUGHT, "firm:1") == 12.0 - 2.0 - 3.0)
check("a taught trade has a pool", make_world().free_fte(TAUGHT, "firm:1") is not None)
world = make_world()
world._sim.labour.available = False
check("a trade that is not available stays without a pool", world.free_fte(TAUGHT, "firm:1") is None)
check("when the founder and others hold all of it, none is free", make_world(taught=4.0).free_fte(TAUGHT, "firm:1") == 0.0)
check("a trade people practise already is drawn from the whole country's people", make_world().free_fte("smith", "firm:1") == 1000.0 - 5.0 - 0.0)


class Firm:
    actor_id = "firm:1"
    workforce = {}

    def __init__(self):
        self.workforce = {}

    def capacity_of(self, node_id):
        return 1.0


class StaffWorld:
    def __init__(self, free):
        self.free = free

    def concern_staff(self, node_id):
        return {TAUGHT: 4.0}

    def free_fte(self, trade, actor_id):
        return self.free


firm = Firm()
check("a firm with no taught people to draw on finds none of its staff", concern_ops.staff_concern(firm, "mill", StaffWorld(0.0)) == 0.0)
firm = Firm()
check("a firm takes the share the pool covers", concern_ops.staff_concern(firm, "mill", StaffWorld(3.0)) == 0.75 and firm.workforce[TAUGHT] == 3.0)
