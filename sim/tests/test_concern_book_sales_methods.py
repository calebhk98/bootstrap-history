"""The production module's book sales on a stand-in game: which concerns put output in the year's clearing and at what scale, and
what their inputs cost at the economy's prices (the estimate leaves a concern out exactly when it sells on the book).
The rules it calls are test_seat_paid_from_sales."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import production_host
from sim.tests.ui_stand_in import Game

TRADED = {"acid"}


def _Game(operating=("mill",), granted=(), ventures=("mill", "school"), baskets=None, economy_prices=None):
    """The module over a stand-in game, with the questions it asks of itself answered as the test says."""
    prices = {"salt": 4.0}
    game = Game(
        state=types.SimpleNamespace(projects=types.SimpleNamespace(operating=set(operating), granted=set(granted))),
        output_factor=0.5, price_index=2.0,
        economy=types.SimpleNamespace(agent_trades_good=lambda good: good in TRADED, agent_prices_at=lambda: economy_prices),
        commodity_record=lambda tag: {}, _material_prices=lambda: prices)
    module = production_host.build(game, capability_sets=(frozenset(), frozenset({"school"}), {}))
    module.is_venture = lambda node_id: node_id in set(ventures)
    module.concern_baskets_now = lambda node_id: baskets
    module.venture_ramp = lambda node_id: 0.8
    module.institution_units = lambda node_id: 3.0
    return module


def baskets(outputs=None, purchases=None):
    return types.SimpleNamespace(outputs=outputs or {}, purchases=purchases or {})


class ScaleTests(unittest.TestCase):
    def test_a_concern_runs_at_its_ramp_times_the_output_factor(self):
        self.assertAlmostEqual(_Game().concern_book_scale("mill"), 0.8 * 0.5)

    def test_a_scalable_institution_also_runs_at_its_units(self):
        self.assertAlmostEqual(_Game().concern_book_scale("school"), 0.8 * 3.0 * 0.5)


class OfferTests(unittest.TestCase):
    def test_only_traded_outputs_are_offered_at_the_scale(self):
        game = _Game(baskets=baskets({"acid": 100.0, "dust": 50.0}))
        self.assertEqual(game.concern_book_offer("mill"), {"acid": 100.0 * 0.4})
        self.assertTrue(game.concern_sells_on_book("mill"))

    def test_a_concern_not_running_offers_nothing(self):
        game = _Game(operating=(), baskets=baskets({"acid": 100.0}))
        self.assertEqual(game.concern_book_offer("mill"), {})
        self.assertFalse(game.concern_sells_on_book("mill"))

    def test_a_concern_the_society_already_ran_offers_nothing(self):
        self.assertEqual(_Game(granted=("mill",), baskets=baskets({"acid": 100.0})).concern_book_offer("mill"), {})

    def test_a_node_that_is_not_a_venture_offers_nothing(self):
        self.assertEqual(_Game(ventures=(), baskets=baskets({"acid": 100.0})).concern_book_offer("mill"), {})

    def test_a_concern_with_no_baskets_offers_nothing(self):
        self.assertEqual(_Game(baskets=None).concern_book_offer("mill"), {})

    def test_a_concern_making_only_untraded_goods_does_not_sell_on_the_book(self):
        self.assertFalse(_Game(baskets=baskets({"dust": 50.0})).concern_sells_on_book("mill"))


class InputsCostTests(unittest.TestCase):
    def test_an_input_the_economy_prices_costs_that_price_at_the_scale(self):
        game = _Game(baskets=baskets(purchases={"ore": 10.0}), economy_prices={"ore": 3.0})
        self.assertAlmostEqual(game.concern_book_inputs_cost("mill"), 10.0 * 0.4 * 3.0)

    def test_an_input_the_economy_lacks_falls_back_to_the_long_run_cost_at_todays_price_level(self):
        game = _Game(baskets=baskets(purchases={"salt": 10.0}), economy_prices={"ore": 3.0})
        self.assertAlmostEqual(game.concern_book_inputs_cost("mill"), 10.0 * 0.4 * 4.0 * 2.0)

    def test_an_input_nothing_prices_is_left_out(self):
        game = _Game(baskets=baskets(purchases={"air": 10.0, "ore": 1.0}), economy_prices={"ore": 3.0})
        self.assertAlmostEqual(game.concern_book_inputs_cost("mill"), 1.0 * 0.4 * 3.0)

    def test_no_baskets_cost_nothing(self):
        self.assertEqual(_Game(baskets=None).concern_book_inputs_cost("mill"), 0.0)

    def test_an_economy_without_prices_still_answers_from_the_long_run_costs(self):
        game = _Game(baskets=baskets(purchases={"salt": 1.0}), economy_prices=None)
        self.assertAlmostEqual(game.concern_book_inputs_cost("mill"), 0.4 * 8.0)


if __name__ == "__main__":
    unittest.main()
