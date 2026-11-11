"""A price needs a seller (Complaints/38, 119).

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
A material no one in reach can make or sell has no price: not a price at the technique that would make
it if every technology were held. The sellers in reach are the home society's producers (a technique it
holds or can reach) and a trading partner that makes it, over a route. Everything here runs on small
fixtures; nothing builds a game or solves the whole tree."""

QUICK_TOPIC = True

import math
import types
import unittest
from unittest import mock

from sim.prices import prices as engine_prices, solve_prices_core
from sim.markets.goods_offers import GoodsOffers, HOME_SELLER
from sim.projects.api import START_CHECKS
from sim.tests import materials_stand_in


def _wage_document():
    return {"wage_rates_denarii_per_hour": {"labourer": {"rate": 2.0}}, "money_per_labour_hour": 2.0}


def _entry(outputs, inputs=None, labour_hours=None, requires_node=None):
    return {"outputs": outputs, "inputs": inputs or {}, "labour_hours": labour_hours or {},
            "requires_node": requires_node}


class NoFallbackPriceTests(unittest.TestCase):

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)

    def test_a_material_only_a_distant_joint_process_makes_is_not_priced_at_the_mature_technique(self):
        entries = {
            "near": _entry({"copper_kg": 1.0}, labour_hours={"labourer": 1.0}, requires_node="near_node"),
            "far_joint": _entry({"copper_kg": 1.0, "zinc_kg": 1.0}, labour_hours={"labourer": 2.0},
                                requires_node="far_node"),
        }
        steps = {"near_node": 1, "far_node": 5}
        with mock.patch.object(engine_prices, "_unheld_steps_to", lambda node, held, mods_dir=None: steps[node]):
            goods, provenance = engine_prices.priced_goods_table(set(), _wage_document(), production_entries=entries)
        self.assertEqual(provenance["copper_kg"], "gated")
        self.assertNotIn("zinc_kg", goods)
        self.assertNotIn("zinc_kg", provenance)

    def test_a_waste_co_product_does_not_shut_out_the_joint_process_that_makes_a_product(self):
        entries = {
            "rear": _entry({"draught_kg": 1.0, "manure_kg": 2.0}, labour_hours={"labourer": 1.0},
                           requires_node="rear_node"),
            "flock": _entry({"wool_kg": 1.0, "manure_kg": 1.0}, labour_hours={"labourer": 1.0},
                            requires_node="flock_node"),
        }
        steps = {"rear_node": 3, "flock_node": 1}
        with mock.patch.object(engine_prices, "_unheld_steps_to", lambda node, held, mods_dir=None: steps[node]):
            goods, provenance = engine_prices.priced_goods_table(set(), _wage_document(), production_entries=entries)
        self.assertEqual(provenance["draught_kg"], "gated")
        self.assertEqual(provenance["wool_kg"], "gated")

    def test_every_label_left_is_a_seller_the_society_has_or_can_reach(self):
        entries = {"hand": _entry({"cloth_kg": 1.0}, labour_hours={"labourer": 1.0}),
                   "loom": _entry({"silk_kg": 1.0}, labour_hours={"labourer": 1.0}, requires_node="loom_node")}
        _goods, provenance = engine_prices.priced_goods_table(set(), _wage_document(), production_entries=entries)
        self.assertEqual(set(provenance.values()), {"solved", "gated"})


def _fake_sim(home_prices, gated=()):
    remembered = {}     # what the market keeps for the acting seat
    return types.SimpleNamespace(
        civ={"id": "home"}, remembered=remembered.get, remember=remembered.__setitem__, not_traded_materials=frozenset,
        border_terms=lambda destination, source: (0.0, False),
        _price_tables=lambda: ({}, {material: ("gated" if material in gated else "solved")
                                    for material in home_prices}),
        materials=types.SimpleNamespace(
            tag=lambda material: (material, material),
            prices=lambda: home_prices,
            price_per_unit=lambda material: home_prices.get(material),
            priced_key=lambda tag, prices: tag if tag in prices else None,
            sold_material=lambda tag: tag),
        year=100, state=types.SimpleNamespace(projects=types.SimpleNamespace()), techniques_held=frozenset,
        finance=types.SimpleNamespace(market_rate=lambda: 0.05),
        economy=types.SimpleNamespace(agent_prices_at=lambda tile=None: None),      # the economy is still opening
    )


class SellerInReachTests(unittest.TestCase):

    def setUp(self):
        self.sim = _fake_sim(home_prices={"wheat_kg": 4.0})

    def test_a_material_the_home_prices_keeps_its_home_seller_and_price(self):
        offers = GoodsOffers(self.sim)
        self.assertEqual(offers.offered_by("wheat_kg"), HOME_SELLER)
        self.assertEqual(offers.household_prices()["wheat_kg"], 4.0)

    def test_a_material_no_one_in_reach_makes_has_no_seller_and_no_price(self):
        offers = GoodsOffers(self.sim)
        self.assertIsNone(offers.offered_by("cobalt_kg"))
        self.assertIsNone(offers.unit_price("cobalt_kg"))
        self.assertFalse(offers.can_be_bought("cobalt_kg"))
        self.assertNotIn("cobalt_kg", offers.household_prices())


class CheapestSellerInReachTests(unittest.TestCase):

    def _sim(self, **keywords):
        return _fake_sim(home_prices={"glass_kg": 40.0, "wheat_kg": 4.0}, **keywords)

    def test_a_partner_that_sells_dearer_leaves_the_gated_home_technique_the_seller(self):
        sim = _fake_sim(home_prices={"glass_kg": 2.0}, gated={"glass_kg"})
        offers = GoodsOffers(sim)
        self.assertEqual(offers.offered_by("glass_kg"), HOME_SELLER)
        self.assertEqual(offers.unit_price("glass_kg"), 2.0)

    def test_a_good_the_home_runs_a_producer_for_stays_with_the_home_even_where_a_partner_is_cheaper(self):
        offers = GoodsOffers(self._sim(gated={"glass_kg"}))
        self.assertEqual(offers.offered_by("wheat_kg"), HOME_SELLER)
        self.assertEqual(offers.unit_price("wheat_kg"), 4.0)


class ProjectNeedsASellerTests(unittest.TestCase):

    NODE = {"mat": {"cobalt_kg": 100.0, "wheat_kg": 10.0}}

    def _project(self, offers, stock_tonnes=0.0):
        return materials_stand_in.build(tree_nodes={"alloy_works": self.NODE}, can_be_bought=offers.can_be_bought,
                                        goods_stock=lambda key: stock_tonnes)

    def _verdict(self, game, why):
        return game.start_gate_material_seller("alloy_works", self.NODE, False, None, why)

    def test_a_project_needing_an_unsold_material_cannot_start_and_says_why(self):
        offers = GoodsOffers(_fake_sim({"wheat_kg": 4.0}))
        verdict = self._verdict(self._project(offers), True)
        self.assertFalse(verdict[0])
        self.assertIn("cobalt_kg", verdict[1])
        self.assertNotIn("wheat_kg", verdict[1])

    def test_the_gate_reports_the_blocker_of_supply(self):
        (check,) = [check for check in START_CHECKS if check.source == "start_gate_material_seller"]
        self.assertEqual((check.cause, check.kind), ("materials_have_a_seller", "supply"))

    def test_the_boolean_answer_needs_no_sentence(self):
        offers = GoodsOffers(_fake_sim({"wheat_kg": 4.0}))
        self.assertEqual(self._verdict(self._project(offers), False), (False, None))

    def test_stock_already_held_needs_no_seller(self):
        offers = GoodsOffers(_fake_sim({"wheat_kg": 4.0}))
        self.assertIsNone(self._verdict(self._project(offers, stock_tonnes=math.inf), True))


class AlternativeEnergyCycleTests(unittest.TestCase):
    """Complaints/119: a photovoltaic panel is built from aluminium, and aluminium is smelted with
    electricity, so the cheaper electricity gets, the cheaper its own source gets. The solver prices
    that loop to a fixed point (the circulating share is small) and picks the panel when it is cheapest."""

    ENTRIES = {
        "bauxite": _entry({"bauxite_kg": 1000.0}, labour_hours={"labourer": 5.0}),
        "aluminium": dict(_entry({"aluminium_kg": 1000.0}, {"bauxite_kg": 4020.0}, {"labourer": 70.0}),
                          electrical_mj=46000.0),
        "muscle": _entry({"mechanical_mj": 1.0}, labour_hours={"labourer": 0.2}),
        "dynamo_unit": _entry({"dynamo_unit": 1.0}, labour_hours={"labourer": 500.0}),
        "panel": _entry({"photovoltaic_panel_m2": 1.0}, {"aluminium_kg": 1.8}, {"labourer": 4.5}),
        "dynamo": dict(_entry({"electricity_generated_mj": 1000.0}, labour_hours={"labourer": 0.1}),
                       mechanical_mj=1081.1,
                       capital=[{"build_materials": {"dynamo_unit": 1.0}, "service_life_years": 20,
                                 "annual_output_at_basis": 116700.0}]),
        "photovoltaic": dict(_entry({"electricity_generated_mj": 1000.0}),
                             capital=[{"build_materials": {"photovoltaic_panel_m2": 1.0}, "service_life_years": 25,
                                       "annual_output_at_basis": 1180.0}]),
        "line": _entry({"electrical_mj": 1000.0}, {"electricity_generated_mj": 1321.5}, {"labourer": 0.05}),
    }

    def test_the_loop_resolves_and_the_solve_converges_well_inside_the_iteration_limit(self):
        producers = solve_prices_core.build_producers_index(self.ENTRIES)
        resolvable = solve_prices_core.compute_resolvable_materials(self.ENTRIES, producers)
        self.assertIn("photovoltaic_panel_m2", resolvable)
        prices, iterations, residual, chosen = solve_prices_core.solve(
            self.ENTRIES, producers, resolvable, {"labourer": 1.0}, interest_rate=0.05)
        self.assertLess(residual, solve_prices_core.CONVERGENCE_TOLERANCE)
        self.assertLess(iterations, solve_prices_core.MAXIMUM_ITERATIONS // 10)
        self.assertEqual(chosen["electricity_generated_mj"], "photovoltaic")
        self.assertTrue(all(math.isfinite(price) and price > 0.0 for price in prices.values()))

    def test_without_the_panel_technique_the_dynamo_is_chosen(self):
        entries = {key: entry for key, entry in self.ENTRIES.items() if key != "photovoltaic"}
        producers = solve_prices_core.build_producers_index(entries)
        resolvable = solve_prices_core.compute_resolvable_materials(entries, producers)
        _prices, _iterations, _residual, chosen = solve_prices_core.solve(
            entries, producers, resolvable, {"labourer": 1.0}, interest_rate=0.05)
        self.assertEqual(chosen["electricity_generated_mj"], "dynamo")


class PhotovoltaicEntriesAreGatedTests(unittest.TestCase):

    def test_both_photovoltaic_entries_name_the_node_that_makes_their_silicon(self):
        entries = engine_prices.default_production_entries()
        gate = entries["silicon_kg"]["requires_node"]
        for key in ("photovoltaic_panel_m2", "electrical_mj_photovoltaic"):
            self.assertEqual(entries[key].get("requires_node", "absent"), gate, key)


if __name__ == "__main__":
    unittest.main()
