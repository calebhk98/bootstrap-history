"""Complaint 528: the scan of the concerns a society holds for whether they pay their way returns structured figures
that agree with what an entrant weighs. The shape is tested on a fake world (quick); the figures on a test game
(slow topic). Nothing here asserts that any share pays: the share is reported, not gated.

Re-measure: `python3 -m sim.tests --slow --only concerns_that_pay`."""
from .harness import *  # noqa: F401,F403

from sim.agents import concern_scan
from sim.engine import concern_scan_run

FIELDS = {"node", "takings", "upkeep", "wages", "carried", "costs", "margin", "pays"}


class FakeWorld:
    """One concern: takings 10, upkeep 2, wages 3, rent 1, no manager."""
    year = 0
    hours_per_person_year = 1.0

    def entry_gross(self, node_id, rivals, entrants):
        return 10.0 if node_id == "pays" else 4.0

    def upkeep(self, node_id, capacity=1.0):
        return 2.0

    def concern_wage_bill(self, node_id, capacity=1.0):
        return 3.0

    def site_rent(self, node_id, capacity=1.0, tile=None):
        return 1.0

    def concern_staff(self, node_id):
        return {}


class FakeRegistry:
    actors = {}

    class state:
        home_country = None


rows = concern_scan.scan(FakeRegistry(), FakeWorld(), ["loses", "pays"])
check("a scanned concern carries takings and each cost as structured values", all(set(row) == FIELDS for row in rows),
      [sorted(row) for row in rows])
by_node = {row["node"]: row for row in rows}
check("costs are upkeep plus wages plus what a firm carries", by_node["pays"]["costs"] == 6.0, by_node["pays"])
check("a concern pays when its takings exceed its costs",
      by_node["pays"]["pays"] and not by_node["loses"]["pays"], by_node)
summary = concern_scan.summary(rows)
check("the summary counts the concerns that pay and lists payers and losers",
      (summary["count"], summary["paying"]) == (2, 1) and [row["node"] for row in summary["pay"]] == ["pays"]
      and [row["node"] for row in summary["losers"]] == ["loses"], summary)
check("an empty scan has no share", concern_scan.summary([])["share"] is None)

# SCENARIO (wiring): the scan reads the concerns a real society holds. The pay rule, the cost sum and the summary are
# held above on the fake world; "a row's takings and costs are the entry test's figures" is the same sum with
# SimWorld's own methods, so it is not repeated here.
game = sim()
held = concern_scan_run.held_concerns(game)
result = concern_scan_run.scan_game(game)
check("scenario: the scan covers every concern the society holds, each row carrying the fields",
      result["count"] == len(held) and len(held) > 0
      and all(set(row) == FIELDS for row in result["pay"] + result["losers"]), (result["count"], len(held)))
