"""Complaint 659: the opening and the post-spin-up trim keep the people a trade's booked hours need, and the
plot trade is the one households' own land asks most of even when its recipes carry the wear of their tools.
Rules called on built inputs (labour_state.plot_trade, opening_state, workforce_settle.trim_people)."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import labour_state, workforce_settle
from sim.economy.types import Recipe
from sim.labour.market import aptitude, opening, records, trades

HOURS = 2000.0
REGISTRY = {
    "labourer": {"family": "toil", "training_years": 0, "fallback": True},
    "farmer": {"family": "toil", "training_years": 1},
    "smith": {"family": "craft", "training_years": 3},
}


class PlotTradeTests(unittest.TestCase):
    def setup_with(self, wheat_inputs, wheat_wear):
        recipes = {
            "wheat": Recipe("wheat", {"grain": 1.0}, wheat_inputs, {"farmer": 100.0}, tool_wear=wheat_wear),
            "hammer": Recipe("hammer", {"tool": 1.0}, {}, {"smith": 90.0}),
        }
        return SimpleNamespace(recipes=recipes, land_per_run={"wheat": 1.0})

    def test_a_crop_whose_only_bought_input_is_its_workers_tools_is_still_own_plot_work(self):
        setup = self.setup_with({"tool": 0.2}, {"tool": 0.2})
        self.assertEqual(labour_state.plot_trade(setup), "farmer")

    def test_a_crop_with_another_bought_input_is_not_own_plot_work(self):
        setup = self.setup_with({"tool": 0.2, "seed": 1.0}, {"tool": 0.2})
        self.assertEqual(labour_state.plot_trade(setup), "")


class SmithHoursKeepTheirPeopleTests(unittest.TestCase):
    def setUp(self):
        self.specs = trades.trade_specs(REGISTRY)
        self.smith_hours = 400 * HOURS
        self.wanted = {("vale", "smith"): self.smith_hours, ("vale", "labourer"): 100 * HOURS}
        self.state = opening.opening_state(self.specs, {"vale": 10000.0},
                                           {"vale": {"smith": self.smith_hours, "labourer": 100 * HOURS}}, HOURS, "farmer")

    def test_the_opening_places_the_smiths_the_booked_hours_take(self):
        self.assertAlmostEqual(aptitude.band_total(self.state.workers["vale"]["smith"]), 400.0)

    def test_the_trim_to_the_hours_wanted_keeps_them(self):
        workforce_settle.trim_people(self.state, self.wanted, "labourer", HOURS)
        workforce_settle.send_idle_to_plots(self.state, self.wanted, "labourer", "farmer", HOURS)
        self.assertAlmostEqual(aptitude.band_total(self.state.workers["vale"]["smith"]), 400.0)

    def test_the_plot_trade_takes_everyone_else_and_nobody_is_lost(self):
        self.assertAlmostEqual(records.people_in(self.state), 10000.0)
        self.assertAlmostEqual(aptitude.band_total(self.state.workers["vale"]["farmer"]), 10000.0 - 400.0 - 100.0)


if __name__ == "__main__":
    unittest.main()
