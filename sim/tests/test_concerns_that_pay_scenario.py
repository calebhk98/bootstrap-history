"""SCENARIO (Complaint 640): Complaints 528 and 510, the scan of a society's plants on a real game. The pay rule, the cost
sum and the summary are called on a fake world in test_concerns_that_pay."""
from .harness import *  # noqa: F401,F403

from sim.engine import concern_scan_run

FIELDS = {"node", "owner", "size", "sells", "takings", "upkeep", "wages", "carried", "costs", "margin", "pays"}

# SCENARIO (wiring): the scan reads one plant of each concern a real society holds, and the plants its owners run. The pay
# rule, the cost sum and the summary are held above on the fake world; "a row's takings and costs are the entry test's
# figures" is the same sum with SimWorld's own methods, so it is not repeated here.
game = unopened_sim()
held = concern_scan_run.held_concerns(game)
result = concern_scan_run.scan_game(game)
check("scenario: the scan covers every concern the society holds, each row carrying the fields",
      result["count"] == len(held) and len(held) > 0
      and all(set(row) == FIELDS for row in result["pay"] + result["losers"]), (result["count"], len(held)))
# the opening runs nothing, so the founder opens one concern and the scan must then read exactly the plants that run
node_id = next(node for node in game.order if NODES[node]["rev"] > 0 and game.is_venture(node)
               and game.staffing_open_refusal(node) is None)
game.state.projects.done.add(node_id)
opened, reason = game.open_venture(node_id, pay=False)
running = concern_scan_run.scan_game(game)["running"]
operating = {entry_key for _owner, business in concern_scan_run.running_businesses(game)
             for entry_key in business.operating()}
check("scenario: the plants the owners run now are scanned too, each with its owner",
      opened and len(operating) > 0 and running["count"] == len(operating)
      and all(row["owner"] for row in running["pay"] + running["losers"]),
      (opened, reason, running["count"], len(operating)))
