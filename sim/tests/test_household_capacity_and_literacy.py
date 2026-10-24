"""How many people a household can staff at all: the ceiling literacy puts on lettered trades
(`literate_capacity`), the household room (`household_room`) and the advice that points at what would widen it
(`_room_advice`). Complaint 640: the rules are called on a stub world built here."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.labour.labour_capacity import CapacityMixin
from sim.refusal import facts_of


class _StubLabour(CapacityMixin):
    """Only what the capacity rules read."""
    LITERATE_TRADES = frozenset({"machinist", "scholar"})
    LITERATE_CAPACITY_FLOOR = 2.0

    def __init__(self, literacy=1.0, institutional=0.0, supervision=0.0, headcount_now=0.0, room_places=0.0,
                 existing=None, absent=(), done=(), operating=(), room_sources=()):
        projects = types.SimpleNamespace(done=set(done), operating=set(operating))
        self._world = types.SimpleNamespace(
            cfg={"hired_hours_cap_base": 1000000.0}, pop_scale=1.0, HOURS_PER_PERSON_YEAR=2000.0,
            trades_absent=set(absent), state=types.SimpleNamespace(projects=projects),
            ROOM_SOURCES=list(room_sources), nodes={node_id: {} for node_id, _ in room_sources},
            is_venture=lambda node_id: True, is_visible=lambda node_id: True,
            closure=lambda nodes, node_id: {node_id}, start_reason=lambda node_id, _why=True: (True, ""),
            money_text=lambda amount, grouped=False: "%g" % amount, housing_price_per_place=lambda: 100.0)
        self.literacy, self.institutional, self.supervision = literacy, institutional, supervision
        self.headcount_now, self.room_places, self.existing = headcount_now, room_places, existing

    def local_market_share(self):
        return 1.0

    def literacy_factor(self, trade):
        return self.literacy

    def staff_capacity(self):
        return self.institutional, self.room_places

    def supervision_room(self):
        return self.supervision

    def headcount(self):
        return self.headcount_now

    def people_who_exist(self, trade):
        return float("inf") if self.existing is None else self.existing

    def room_added_by(self, places):
        return places


# --- literate_capacity: the ceiling on lettered trades.
_low = _StubLabour(literacy=0.2).literate_capacity("machinist")
_high = _StubLabour(literacy=0.9).literate_capacity("machinist")
check("teaching a society to read raises what it can staff", _high > _low, (_low, _high))
_floor = _StubLabour.LITERATE_CAPACITY_FLOOR
check("...in proportion to literacy above the floor, not without bound",
      abs((_StubLabour(literacy=0.6).literate_capacity("machinist") - _floor)
          - 2.0 * (_StubLabour(literacy=0.3).literate_capacity("machinist") - _floor)) < 1e-9)
check("a trade that needs no letters is not capped by literacy at all",
      _StubLabour().literate_capacity("smith") == float("inf"))
check("a floor of findable people stays when no one reads", _StubLabour(literacy=0.0).literate_capacity("machinist")
      == _StubLabour.LITERATE_CAPACITY_FLOOR)
check("the floor is added to, not maxed with, the pool: reading still moves the ceiling",
      _StubLabour(literacy=0.01).literate_capacity("machinist") > _StubLabour(literacy=0.0).literate_capacity("machinist"))
check("a scholar ceiling adds the institutions that train scholars outright",
      _StubLabour(institutional=7.0).literate_capacity("scholar") > _StubLabour().literate_capacity("scholar") + 6.9)
check("only a scholar gets the institutional pool", _StubLabour(institutional=7.0).literate_capacity("machinist")
      == _StubLabour().literate_capacity("machinist"))
check("the people who exist cap a present trade", _StubLabour(existing=1.5).literate_capacity("machinist") == 1.5)
check("...but not a trade the world has none of yet (absent trades are taught in)",
      _StubLabour(existing=0.0, absent={"machinist"}).literate_capacity("machinist") > 0.0)

# --- household_room: one number for hire, buy and train.
check("household room is the places plus the supervision, less the people held",
      _StubLabour(room_places=8.0, supervision=4.0, headcount_now=5.0).household_room() == 7.0)
check("...and goes negative when more are held than there is room for",
      _StubLabour(room_places=3.0, supervision=0.0, headcount_now=5.0).household_room() == -2.0)

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
