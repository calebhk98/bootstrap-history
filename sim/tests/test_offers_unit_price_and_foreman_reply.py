"""Rule tests on stand-ins (Complaints 38, 145, 154, 640): a material no one in reach sells has no unit price and cannot
be bought; a venture's `why` reply carries the specialist foreman `open` demands; the floor-left input counts what is left
of an active project."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.critical_path_remaining import active_years_left
from sim.markets.goods_offers import GoodsOffers
from sim.ui.proto.techtree import _staffing_standing_crew


class UnitPriceTests(unittest.TestCase):
    def test_a_material_no_home_technique_and_no_partner_makes_has_no_unit_price(self):
        market = types.SimpleNamespace(offered_by=lambda material: None, home_unit_price=lambda material: None,
                                       household_prices=lambda: {})
        self.assertIsNone(GoodsOffers.unit_price(market, "cobalt_kg"))

    def test_a_material_with_no_unit_price_cannot_be_bought(self):
        market = types.SimpleNamespace(unit_price=lambda material: None)
        self.assertFalse(GoodsOffers.can_be_bought(market, "cobalt_kg"))

    def test_a_material_with_a_unit_price_can_be_bought(self):
        market = types.SimpleNamespace(unit_price=lambda material: 2.5)
        self.assertTrue(GoodsOffers.can_be_bought(market, "cobalt_kg"))


class ForemanReplyTests(unittest.TestCase):
    def test_the_standing_crew_reply_carries_the_foreman_trade_fte_and_who_is_free(self):
        sim = types.SimpleNamespace(venture_foreman_free=lambda trade: 3.14159, opening_fee=lambda node_id: (10.0,))
        reply = _staffing_standing_crew(sim, "node", True, 1.0, 2.0, 5.0, 5.0, "smith", 0.5)
        self.assertEqual(reply["specialist_foreman_to_keep_it_open"], {"trade": "smith", "fte": 0.5, "free_now": 3.14})

    def test_the_standing_crew_reply_has_no_foreman_when_the_concern_needs_none(self):
        sim = types.SimpleNamespace(venture_foreman_free=lambda trade: 0.0, opening_fee=lambda node_id: (10.0,))
        reply = _staffing_standing_crew(sim, "node", True, 1.0, 2.0, 5.0, 5.0, None, 0.0)
        self.assertIsNone(reply["specialist_foreman_to_keep_it_open"])


class ActiveYearsLeftTests(unittest.TestCase):
    NODES = {"a": {"yrs": 4.0, "ph": 20000.0}}

    def test_an_active_project_has_the_larger_of_floor_left_and_hours_left(self):
        left = active_years_left(self.NODES, {"a": {"yrs": 1.0, "ph_left": 2000.0}})
        self.assertEqual(left, {"a": 3.0})
        left = active_years_left(self.NODES, {"a": {"yrs": 3.5, "ph_left": 4000.0}})
        self.assertEqual(left, {"a": 2.0})

    def test_an_active_project_the_tree_does_not_know_is_left_out(self):
        self.assertEqual(active_years_left(self.NODES, {"zzz": {"yrs": 0.0}}), {})


if __name__ == "__main__":
    unittest.main()
