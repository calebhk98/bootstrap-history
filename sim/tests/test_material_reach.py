"""How a material reaches the founder (material_reach.py): imports count as market supply, and a good with
no supply says why. Small fixtures only."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine.goods_market_imports import HOME_SELLER
from sim.engine.material_reach import MaterialReachMixin


class _Market:
    def __init__(self, seller, left, priced=True):
        self._seller, self._left, self._priced = seller, left, priced

    def offered_by(self, material):
        return self._seller

    def import_tonnes_available(self, material, partner=None):
        return self._left

    def can_be_bought(self, material):
        return self._priced


class _Founder(MaterialReachMixin):
    def __init__(self, market, stock=0.0, own=0.0, market_tonnes=0.0, makers=(), done=(), visible=None):
        self.goods_market = market
        self._visible = visible
        self.nodes = {node_id: {"_output_per_year": {"alum_kg": 1.0}} for node_id in makers}
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(done=set(done)))
        self._stock, self._own, self._market = stock, own, market_tonnes

    def is_visible(self, node_id):
        return self._visible is None or node_id in self._visible

    def _material_tag(self, material):
        return material, "mine:" + material

    def material_stock_t(self, emp_key):
        return self._stock

    def _own_material_supply(self, tag):
        return self._own

    def _material_market_tonnes(self, emp_key):
        return self._market + self._material_import_tonnes(emp_key)

    def foreign_supply_tonnes(self, partner, material):
        return 7.0


class ImportTests(unittest.TestCase):
    def test_a_partners_tonnes_are_what_comes(self):
        self.assertEqual(_Founder(_Market("partner", 12.0))._material_import_tonnes("alum_kg"), 12.0)

    def test_the_home_society_as_seller_brings_no_import(self):
        self.assertEqual(_Founder(_Market(HOME_SELLER, 12.0))._material_import_tonnes("alum_kg"), 0.0)

    def test_no_seller_brings_no_import(self):
        self.assertEqual(_Founder(_Market(None, None))._material_import_tonnes("alum_kg"), 0.0)

    def test_a_route_with_no_lift_limit_brings_what_the_partner_makes(self):
        self.assertEqual(_Founder(_Market("partner", float("inf")))._material_import_tonnes("alum_kg"), 7.0)


class RouteTests(unittest.TestCase):
    def test_a_partner_that_sells_it_makes_it_imported(self):
        self.assertEqual(_Founder(_Market("partner", 3.0)).material_supply_route("alum_kg")["route"], "imported")

    def test_deposits_or_producers_make_it_market(self):
        route = _Founder(_Market(HOME_SELLER, None), market_tonnes=2.0).material_supply_route("alum_kg")["route"]
        self.assertEqual(route, "market")

    def test_stock_or_own_workings_make_it_held(self):
        self.assertEqual(_Founder(_Market(HOME_SELLER, None), stock=1.0).material_supply_route("alum_kg")["route"], "held")
        self.assertEqual(_Founder(_Market(HOME_SELLER, None), own=1.0).material_supply_route("alum_kg")["route"], "held")

    def test_a_priced_good_no_producer_runs_is_makeable_and_says_so(self):
        founder = _Founder(_Market(HOME_SELLER, None))
        self.assertEqual(founder.material_supply_route("alum_kg")["route"], "makeable")
        self.assertIn("No producer runs alum_kg", founder.material_unsupplied_sentence("alum_kg"))

    def test_a_concern_of_the_tree_that_makes_it_is_named(self):
        founder = _Founder(_Market(HOME_SELLER, None), makers=("alum_works",), done=("alum_works",))
        self.assertIn("alum_works", founder.material_unsupplied_sentence("alum_kg"))

    def test_a_maker_the_founder_has_not_heard_of_is_not_named(self):
        founder = _Founder(_Market(HOME_SELLER, None), makers=("alum_works", "secret_works"), visible=("alum_works",))
        sentence = founder.material_unsupplied_sentence("alum_kg")
        self.assertIn("alum_works", sentence)
        self.assertNotIn("secret_works", sentence)
        hidden_only = _Founder(_Market(HOME_SELLER, None), makers=("secret_works",), visible=())
        self.assertNotIn("secret_works", hidden_only.material_unsupplied_sentence("alum_kg"))

    def test_a_good_no_one_sells_is_unavailable_and_says_so(self):
        founder = _Founder(_Market(None, None, priced=False))
        self.assertEqual(founder.material_supply_route("alum_kg")["route"], "unavailable")
        self.assertIn("cannot be bought", founder.material_unsupplied_sentence("alum_kg"))

    def test_a_supplied_good_has_nothing_to_explain(self):
        self.assertEqual(_Founder(_Market("partner", 3.0)).material_unsupplied_sentence("alum_kg"), "")
