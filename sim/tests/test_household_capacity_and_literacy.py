"""How many people a household can staff at all: the ceiling literacy puts on lettered trades
(`literate_capacity`), the household room (`household_room`) and the advice that points at what would widen it
(`_room_advice`). Complaint 640: the rules are called on a stub world built here."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.labour.labour_advice import Advice
from sim.labour.labour_capacity import Capacity
from sim.labour.labour_supply import Supply
from sim.refusal import facts_of


class _StubLabour:
    """The neighbours the capacity rules read (book, trades, settlement, capacity), with the supply, capacity and advice parts built over it."""
    LITERATE_TRADES = frozenset({"machinist", "scholar"})

    def __init__(self, literacy=1.0, institutional=0.0, supervision=0.0, headcount_now=0.0, room_places=0.0,
                 posted=0.0, absent=(), done=(), operating=(), room_sources=()):
        projects = types.SimpleNamespace(done=set(done), operating=set(operating))
        nodes = {node_id: {} for node_id, _ in room_sources}
        self._world = types.SimpleNamespace(
            projects=projects, game=types.SimpleNamespace(money_text=lambda amount, grouped=False: "%g" % amount),
            people=types.SimpleNamespace(pop_scale=1.0),
            trades=types.SimpleNamespace(HOURS_PER_PERSON_YEAR=2000.0, trades_absent=set(absent)),
            scenario=types.SimpleNamespace(nodes=nodes, closure=lambda node_id: {node_id}),
            knowledge=types.SimpleNamespace(ROOM_SOURCES=list(room_sources), is_venture=lambda node_id: True,
                                            is_visible=lambda node_id: True, start_reason=lambda node_id, _why=True: (True, "")),
            finance=types.SimpleNamespace(housing_price_per_place=lambda: 100.0))
        self.literacy, self.institutional, self.supervision = literacy, institutional, supervision
        self.headcount_now, self.room_places, self.posted = headcount_now, room_places, posted
        self.supply = Supply(self._world, book=self, capacity=self, settlement=self, trades=self)
        self.supply._people_of_trade_in_reach = lambda trade: 10.0
        self.capacity = Capacity(self._world, book=self, market=None, schedule=None, trades=self)
        self.capacity.staff_capacity = self.staff_capacity
        self.capacity.supervision_room = self.supervision_room
        self.advice = Advice(self._world, capacity=self, hands=None)

    def literate_capacity(self, trade):
        return self.supply.literate_capacity(trade)

    def household_room(self):
        return self.capacity.household_room()

    def _room_advice(self):
        return self.advice.room_advice()

    def literacy_factor(self, trade):
        return self.literacy

    def staff_capacity(self):
        return self.institutional, self.room_places

    def supervision_room(self):
        return self.supervision

    def headcount(self):
        return self.headcount_now

    def staff_posted(self):
        return self.posted

    def room_added_by(self, places):
        return places


# --- literate_capacity: the ceiling on lettered trades.
_low = _StubLabour(literacy=0.2).literate_capacity("machinist")
_high = _StubLabour(literacy=0.9).literate_capacity("machinist")
check("teaching a society to read raises what it can staff", _high > _low, (_low, _high))
_floor = Supply.LITERATE_CAPACITY_FLOOR
check("...in proportion to literacy above the floor, not without bound",
      abs((_StubLabour(literacy=0.6).literate_capacity("machinist") - _floor)
          - 2.0 * (_StubLabour(literacy=0.3).literate_capacity("machinist") - _floor)) < 1e-9)
check("a trade that needs no letters is not capped by literacy at all",
      _StubLabour().literate_capacity("smith") == float("inf"))
check("a floor of findable people stays when no one reads", _StubLabour(literacy=0.0).literate_capacity("machinist")
      == Supply.LITERATE_CAPACITY_FLOOR)
check("the floor is added to, not maxed with, the pool: reading still moves the ceiling",
      _StubLabour(literacy=0.01).literate_capacity("machinist") > _StubLabour(literacy=0.0).literate_capacity("machinist"))
check("a scholar ceiling adds the institutions that train scholars outright",
      _StubLabour(institutional=7.0).literate_capacity("scholar") > _StubLabour().literate_capacity("scholar") + 6.9)
check("only a scholar gets the institutional pool", _StubLabour(institutional=7.0).literate_capacity("machinist")
      == _StubLabour().literate_capacity("machinist"))

# --- household_room: one number for hire, buy and train.
check("household room is the places plus the supervision, less the people held",
      _StubLabour(room_places=8.0, supervision=4.0, headcount_now=5.0).household_room() == 7.0)
check("...and goes negative when more are held than there is room for",
      _StubLabour(room_places=3.0, supervision=0.0, headcount_now=5.0).household_room() == -2.0)

check("...and the people already posted in the labour core take their room too, so no verb spends it twice",
      _StubLabour(room_places=8.0, supervision=4.0, headcount_now=5.0, posted=3.0).household_room() == 4.0)

# --- advice: what raises the room, with a shut source offered back as the cheap fix.
_sources = [("school_founded", 5), ("workshop_first", 3)]
_shut = _StubLabour(done={"school_founded"}, operating=set(), room_sources=_sources)._room_advice()
_open = _StubLabour(done={"school_founded"}, operating={"school_founded"}, room_sources=_sources)._room_advice()
check("a shut room-source is offered back as the cheap fix, not silently dropped from the advice",
      {"action": "reopen", "node": "school_founded"} in facts_of(_shut)["remedies"], facts_of(_shut))
check("...and an open one is not offered for reopening",
      {"action": "reopen", "node": "school_founded"} not in facts_of(_open)["remedies"], facts_of(_open))
check("a source not yet built is offered to build, and the nearest first",
      [remedy["node"] for remedy in facts_of(_open)["remedies"] if remedy["action"] == "build"] == ["workshop_first"],
      facts_of(_open))
check("the room advice always offers to buy housing",
      all({"action": "buy_housing", "node": None} in facts_of(advice)["remedies"] for advice in (_shut, _open)))
_everything = _StubLabour(done={"school_founded", "workshop_first"}, operating={"school_founded", "workshop_first"},
                          room_sources=_sources)._room_advice()
check("with every source built and running only housing remains", facts_of(_everything)["remedies"] == [
      {"action": "buy_housing", "node": None}], facts_of(_everything))
