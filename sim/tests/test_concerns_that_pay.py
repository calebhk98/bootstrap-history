"""Complaint 528: the scan of the concerns a society holds for whether they pay their way returns structured figures
that agree with what an entrant weighs, tested on a fake world; the scan on a real game is
test_concerns_that_pay_scenario. Nothing here asserts that any share pays: the share is reported, not gated."""
QUICK_TOPIC = True
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

    def plant_costs(self, node_id):
        return 2.0, 3.0

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
