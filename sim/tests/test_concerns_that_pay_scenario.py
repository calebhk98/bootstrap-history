"""SCENARIO (Complaint 640): Complaint 528, the scan of the concerns a society holds, on a real game. The pay rule, the cost
sum and the summary are called on a fake world in test_concerns_that_pay."""
from .harness import *  # noqa: F401,F403

from sim.engine import concern_scan_run

FIELDS = {"node", "takings", "upkeep", "wages", "carried", "costs", "margin", "pays"}

# SCENARIO (wiring): the scan reads the concerns a real society holds. The pay rule, the cost sum and the summary are
# held above on the fake world; "a row's takings and costs are the entry test's figures" is the same sum with
# SimWorld's own methods, so it is not repeated here.
game = sim()
held = concern_scan_run.held_concerns(game)
result = concern_scan_run.scan_game(game)
check("scenario: the scan covers every concern the society holds, each row carrying the fields",
      result["count"] == len(held) and len(held) > 0
      and all(set(row) == FIELDS for row in result["pay"] + result["losers"]), (result["count"], len(held)))
