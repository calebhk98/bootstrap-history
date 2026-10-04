"""A newcomer is built to the trade it can see and the supply its plant and inputs can get, not to the whole
gap buyers left."""
import unittest

from sim.economy import entry, entry_sizing
from sim.economy.types import Recipe
from sim.tests.test_economy_producers import View

SALT = Recipe("boil_salt", {"salt": 10.0}, {"firewood": 5.0}, {"hand": 2.0}, {"pan": 1.0}, {}, 10.0)


def market(unmet):
    return {("salt", "area"): entry.UnmetDemand("salt", "area", "anchor", unmet)}


def view():
    return View(prices={"salt": 1.0, "firewood": 0.1, "pan": 2.0}, wages={"hand": 0.2})


def plans(unmet, volumes):
    """volumes: good -> traded last year; a good left out has no market."""
    return entry.entry_plans({"boil_salt": SALT}, view(), market(unmet), None, None,
                             lambda good, tile: volumes.get(good))


class EntrantSizingTests(unittest.TestCase):
    def test_a_gap_far_beyond_the_trade_is_sized_to_the_trade(self):
        # buyers wanted 1e6 more salt, but only 200 was traded: the works is built for a share of the 200
        chosen = plans(1e6, {"salt": 200.0, "firewood": 1e9, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_TRADED_VOLUME * 200.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_a_gap_inside_the_trade_keeps_its_share(self):
        chosen = plans(100.0, {"salt": 1e6, "firewood": 1e9, "pan": 1e9})
        self.assertAlmostEqual(chosen[0].runs, 100.0 * entry.ENTRY_SHARE_OF_UNMET_DEMAND / SALT.outputs["salt"])

    def test_scarce_plant_goods_set_the_size_that_is_built(self):
        # only 3 pans traded: the plant, and so the loan, is for what can be bought, not for the whole plan
        chosen = plans(1e6, {"salt": 1e9, "firewood": 1e9, "pan": 3.0})
        expected = entry_sizing.ENTRY_SHARE_OF_INPUT_VOLUME * 3.0 / SALT.plant_goods["pan"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_scarce_inputs_set_the_size(self):
        chosen = plans(1e6, {"salt": 1e9, "firewood": 20.0, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_INPUT_VOLUME * 20.0 / SALT.inputs["firewood"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_a_market_that_traded_nothing_gets_a_trial_size_not_the_gap(self):
        chosen = plans(1000.0, {"salt": 0.0, "firewood": 1e9, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_UNTRADED_DEMAND * 1000.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_untraded_inputs_give_the_trial_size_too(self):
        chosen = plans(1000.0, {"salt": 1e9, "firewood": 0.0, "pan": 0.0})
        expected = entry_sizing.ENTRY_SHARE_OF_UNTRADED_DEMAND * 1000.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_goods_with_no_market_do_not_limit(self):
        chosen = plans(100.0, {"salt": 1e6})
        self.assertAlmostEqual(chosen[0].runs, 100.0 * entry.ENTRY_SHARE_OF_UNMET_DEMAND / SALT.outputs["salt"])


if __name__ == "__main__":
    unittest.main()
