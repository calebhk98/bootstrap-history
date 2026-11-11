"""Complaint 644: a trade whose work is a service forms from the trade it is taught from. Functions called on built recipes, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour import trade_formation as formation

RECIPES = {
    "bar": {"outputs": {"bar": 1}, "inputs": {"ore": 2, "fuel": 2}, "labour_hours": {"smith": 10.0}},
    "grain": {"outputs": {"grain": 1}, "labour_hours": {"farmer": 5.0}},
    "attendance": {"outputs": {"attendance_hour": 1}, "service": True, "labour_hours": {"steward": 1.0}},
    "luck": {"outputs": {"luck_hour": 1}, "service": True, "labour_hours": {"gambler": 1.0}},
    "tend": {"outputs": {"tend_hour": 1}, "service": True, "labour_hours": {"smith": 2.0}},
}
SHARES = formation.task_shares_by_trade(RECIPES, {})
LINKED = formation.task_shares_by_trade(RECIPES, {"steward": "smith", "smith": "farmer"})

check("a service trade with no parent keeps a task of its own", SHARES["steward"] == {"extract:attendance_hour": 1.0}, SHARES["steward"])
check("a service trade with no parent is uncovered by every other trade",
      formation.uncovered_share(SHARES["steward"], SHARES["smith"]) == 1.0)
check("a service trade does its parent's tasks", LINKED["steward"] == {"ore": 0.5, "fuel": 0.5}, LINKED["steward"])
check("a service trade taught from a parent is covered by the parent's tasks",
      abs(formation.uncovered_share(LINKED["steward"], LINKED["smith"]) - 1.0 / 6.0) < 1e-9)
check("a parent with no goods work lends nothing", formation.task_shares_by_trade(RECIPES, {"gambler": "steward"})["gambler"]
      == {"extract:luck_hour": 1.0})
check("a parent that is not a trade lends nothing", formation.task_shares_by_trade(RECIPES, {"gambler": "nobody"})["gambler"]
      == {"extract:luck_hour": 1.0})
check("a trade with goods work and service work splits its hours by booking",
      abs(LINKED["smith"]["extract:grain"] - 2.0 / 12.0) < 1e-9 and abs(sum(LINKED["smith"].values()) - 1.0) < 1e-9, LINKED["smith"])
check("a trade with goods work keeps its own goods tasks apart from the service ones",
      abs(LINKED["smith"]["ore"] - 5.0 / 12.0) < 1e-9, LINKED["smith"])
check("a taught-from trade starts nearer its parent than an unlinked one",
      formation.nearest_sources("steward", LINKED, ["smith", "farmer"])[0][1] == "smith"
      and formation.nearest_sources("steward", SHARES, ["smith", "farmer"])[0][0] == 1.0)
check("shares keyed on the links are not served to a call without them",
      formation.task_shares_for(RECIPES, {"steward": "smith"})["steward"] == {"ore": 0.5, "fuel": 0.5}
      and formation.task_shares_for(RECIPES)["steward"] == {"extract:attendance_hour": 1.0})
