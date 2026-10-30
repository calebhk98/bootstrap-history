"""How a material reaches the founder (sim/materials/supply.py): imports count as market supply, and a good with
no supply says why. The module over small fixtures."""

QUICK_TOPIC = True

import unittest

from sim.tests import materials_stand_in

HOME = "home"


def _Market(seller, left, priced=True):
    """What the module reads of the market: the tonnes a partner brings (none when the home society or no one sells)."""
    return {"partner_import_tonnes": lambda material: 0.0 if seller in (None, HOME) else left,
            "can_be_bought": lambda material: priced}


def _Founder(market, stock=0.0, own=0.0, market_tonnes=0.0, makers=(), done=(), visible=None):
    module = materials_stand_in.build(
        tree_nodes={node_id: {"_output_per_year": {"alum_kg": 1.0}} for node_id in makers},
        projects_record=materials_stand_in.projects(done=done), goods_stock=lambda commodity: stock,
        mine_capacity={"alum_kg": own},
        visibility=lambda node_id, memo=None: visible is None or node_id in visible, **market)
    module.market_tonnes = lambda commodity: market_tonnes + module.import_tonnes(commodity)
    return module


HOME_SELLER = HOME


class ImportTests(unittest.TestCase):
    def test_a_partners_tonnes_are_what_comes(self):
        self.assertEqual(_Founder(_Market("partner", 12.0)).import_tonnes("alum_kg"), 12.0)

    def test_the_home_society_as_seller_brings_no_import(self):
        self.assertEqual(_Founder(_Market(HOME_SELLER, 12.0)).import_tonnes("alum_kg"), 0.0)

    def test_no_seller_brings_no_import(self):
        self.assertEqual(_Founder(_Market(None, None)).import_tonnes("alum_kg"), 0.0)


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
