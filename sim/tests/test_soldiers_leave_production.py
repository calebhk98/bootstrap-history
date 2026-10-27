"""Complaint 314: people under arms leave the society's labour allocation, so the hours it can put into farm work and
trades fall by their hours, the unskilled fallback trade is needed for their hours and its wage moves by tightness. The
rules are called on a stub game over the real allocation mixin and on the allocation functions; the nationwide count that
includes the army is test_army_in_nationwide_staff."""

QUICK_TOPIC = True

import pathlib
from types import SimpleNamespace

from .harness import check

from sim.labour import labour_allocation, wages
from sim.labour.legacy_trade_defaults import DRAWN_FROM_UNSKILLED_POOL

HOURS = labour_allocation.HOURS_PER_FARM_WORKER_YEAR
FARM = labour_allocation.FARM_TRADE
FALLBACK = "labourer"
SOLDIER = sorted(DRAWN_FROM_UNSKILLED_POOL)[0]


class Allocation(labour_allocation.LabourAllocationMixin):
    """The mixin over a stub world: `staff` is the nationwide head count of each trade the actors hold."""

    def __init__(self, working_age, staff):
        self._world = SimpleNamespace(
            wages={SOLDIER: 1.0, "smith": 1.0, FALLBACK: 1.0}, actors_staff_nationwide=lambda trade: staff.get(trade, 0.0),
            population=SimpleNamespace(working_age=working_age),
            society=SimpleNamespace(society_labour_hours={FARM: 500.0 * HOURS, "smith": 100.0 * HOURS}),
            farm_holdings=lambda: {"hours_needed": 400.0 * HOURS})

    def _non_farm_need_shares(self):
        return {"smith": 1.0}

    def unskilled_trade(self):
        return FALLBACK


# ---- who is under arms -------------------------------------------------------------------------------------------
check("the people under arms are the nationwide staff of the trades drawn from the unskilled pool",
      Allocation(1000.0, {SOLDIER: 120.0})._people_under_arms() == 120.0)
check("staff of a skilled trade are not under arms", Allocation(1000.0, {"smith": 50.0})._people_under_arms() == 0.0)
check("nobody is under arms without a standing army", Allocation(1000.0, {})._people_under_arms() == 0.0)

# ---- the hours that leave production ----------------------------------------------------------------------------
check("the society's hours are the working age less the people under arms, at a farm worker's hours a year",
      Allocation(1000.0, {SOLDIER: 200.0})._society_hours_available() == 800.0 * HOURS)
check("an army larger than the working age leaves no hours, not negative ones",
      Allocation(100.0, {SOLDIER: 200.0})._society_hours_available() == 0.0)
unarmed, armed = Allocation(1000.0, {}), Allocation(1000.0, {SOLDIER: 200.0})
check("the society's hours fall by the soldiers' hours",
      abs(unarmed._society_hours_available() - armed._society_hours_available() - 200.0 * HOURS) < 1e-6)

# ---- the fallback trade is needed for what they leave undone ----------------------------------------------------
check("the soldiers' hours are demand on the unskilled fallback trade, on top of the allocation's need",
      abs(armed._hours_needed_for_wages()[FALLBACK] - unarmed._hours_needed_for_wages().get(FALLBACK, 0.0) - 200.0 * HOURS) < 1e-6,
      (armed._hours_needed_for_wages(), unarmed._hours_needed_for_wages()))
check("a trade other than the fallback is needed for no more with the army out",
      armed._hours_needed_for_wages()["smith"] == unarmed._hours_needed_for_wages()["smith"])
held_hours = 800.0 * HOURS
loose = wages.adjusted_tightness_factor(1.0, 600.0 * HOURS, held_hours)
tight = wages.adjusted_tightness_factor(1.0, 600.0 * HOURS + 200.0 * HOURS, held_hours)
check("with the army out of production the fallback trade's tightness factor ends higher", tight > loose, (tight, loose))

# ---- the fallback trade gets the hours left after the farm and the specialists ------------------------------------
total, farm_hours = 1000.0 * HOURS, 400.0 * HOURS
shares = labour_allocation.shares_from_people({"smith": 100.0, SOLDIER: 0.0}, FALLBACK, total - farm_hours)
hours = labour_allocation.society_hours(total, farm_hours, shares)
check("the hours left after the farm and the specialists go to the fallback trade",
      abs(hours[FALLBACK] - (total - farm_hours - 100.0 * HOURS)) < 1e-6, hours)
check("...and the trades' hours add up to the society's", abs(sum(hours.values()) - total) < 1e-6, hours)

source = pathlib.Path(labour_allocation.__file__).read_text()
check("no content id literal in the allocation module",
      not any(literal in source for literal in ('"soldier"', "'soldier'", '"labourer"', "'labourer'")))
