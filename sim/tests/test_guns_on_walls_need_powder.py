"""A defence credited to guns needs the powder works running (Complaints/245).

A node's `hazard_counters` entry may carry `requires_running`: node ids that
must themselves be running for the counter to count.
"""
import unittest

from .harness import *  # noqa: F401,F403

ARTILLERY = "mil_artillery_piece"
POWDER = "gunpowder"
GUNS_LABEL = "guns on the walls"


def _household(powder_running):
    household = sim(civ="rome_100ad", capital=1e9)
    household.done.update({ARTILLERY, POWDER})
    if powder_running:
        household.operating.add(POWDER)
    household._done_changed()
    household.grant_stock("gunpowder_kg", 3000)
    household.state.household.employees["soldier"] = 40.0
    return household


class GunsOnWallsNeedPowder(unittest.TestCase):

    def test_artillery_counter_declares_the_powder_it_needs(self):
        counters = NODES[ARTILLERY]["mechanics"]["hazard_counters"]
        guns = [counter for counter in counters if counter["label"] == GUNS_LABEL]
        self.assertEqual(guns[0].get("requires_running"), [POWDER])

    def test_guns_lapse_while_the_powder_works_is_closed(self):
        _mult, why = _household(powder_running=False).hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "lapsed" in guns[0], why)

    def test_closing_the_powder_works_weakens_the_defence(self):
        closed = _household(powder_running=False).hazard_relief("sack_chance")[0]
        running = _household(powder_running=True).hazard_relief("sack_chance")[0]
        self.assertGreater(closed, running)

    def test_guns_count_while_the_powder_works_runs(self):
        _mult, why = _household(powder_running=True).hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "lapsed" not in guns[0], why)


class MagazineAndGarrisonInAWholeGame(unittest.TestCase):
    """Whole-game checks of the stock ledger and the labour market (slow; not in the quick tier)."""

    def test_guns_lapse_when_the_magazine_is_empty(self):
        household = _household(powder_running=True)
        household.change_stock("gunpowder_kg", -household.stock_held("gunpowder_kg"))
        _mult, why = household.hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "magazine" in guns[0], why)

    def test_guns_lapse_without_a_crew_hired_from_the_labour_market(self):
        household = _household(powder_running=True)
        household.state.household.employees["soldier"] = 0.0
        _mult, why = household.hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "soldier" in guns[0], why)

    def test_a_year_of_the_running_works_fills_the_magazine(self):
        household = _household(powder_running=True)
        before = household.stock_held("gunpowder_kg")
        household.step_defence_stores()
        self.assertGreater(household.stock_held("gunpowder_kg"), before)


if __name__ == "__main__":
    unittest.main()
