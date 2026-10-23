"""Complaints 528 and 510: the scan of a business's plants for whether they pay their way returns structured figures that
agree with what an entrant weighs, tested on a fake world and a built business; the scan over a game's concerns is
test_concern_scan_run. Nothing here asserts that any share pays: the share is reported, not gated."""
QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.agents import concern_scan
from sim.agents.business import Business

FIELDS = {"node", "owner", "size", "sells", "takings", "upkeep", "wages", "carried", "costs", "margin", "pays"}


class FakeWorld:
    """One plant per unit of size: takings 10, upkeep 2, wages 3, rent 1, no manager; only "pays" sells in the book."""
    year = 0
    hours_per_person_year = 1.0

    def entry_gross(self, node_id, rivals, entrants):
        return 10.0 if node_id == "pays" else 4.0

    def plant_costs(self, node_id):
        return 2.0, 3.0

    def site_rent(self, node_id, capacity=1.0, tile=None):
        return 1.0 * capacity

    def concern_staff(self, node_id):
        return {}

    def sells_on_book(self, node_id):
        return node_id == "pays"


class FakeRegistry:
    actors = {}

    class state:
        home_country = None


business = Business.running(["loses", "pays"])
business.owner_id = "owner"
rows = concern_scan.scan_business(business, FakeRegistry(), FakeWorld())
check("a scanned plant carries its owner, size, whether it sells and each cost as structured values",
      all(set(row) == FIELDS for row in rows), [sorted(row) for row in rows])
by_node = {row["node"]: row for row in rows}
check("costs are upkeep plus wages plus what a firm carries", by_node["pays"]["costs"] == 6.0, by_node["pays"])
check("a plant pays when its takings exceed its costs", by_node["pays"]["pays"] and not by_node["loses"]["pays"], by_node)
check("a row names the owner of the business it was read from", by_node["pays"]["owner"] == "owner", by_node["pays"])
check("a row says whether the plant's goods sell in the book",
      by_node["pays"]["sells"] and not by_node["loses"]["sells"], by_node)

business.set_size("pays", 2.0)
doubled = concern_scan.scan_business(business, FakeRegistry(), FakeWorld())
doubled_by_node = {row["node"]: row for row in doubled}
check("a plant twice the founding size takes and costs twice the figures",
      doubled_by_node["pays"]["takings"] == 20.0 and doubled_by_node["pays"]["costs"] == 12.0, doubled_by_node["pays"])

business.mothball("loses", 0, "test")
check("a mothballed plant is not scanned",
      [row["node"] for row in concern_scan.scan_business(business, FakeRegistry(), FakeWorld())] == ["pays"])

summary = concern_scan.summary(rows)
check("the summary counts the plants that pay and that sell, and lists payers and losers",
      (summary["count"], summary["paying"], summary["selling"]) == (2, 1, 1)
      and [row["node"] for row in summary["pay"]] == ["pays"]
      and [row["node"] for row in summary["losers"]] == ["loses"], summary)
check("an empty scan has no share", concern_scan.summary([])["share"] is None)
