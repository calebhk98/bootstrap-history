"""A price needs a seller (Complaints/38, 119).

A material no one in reach can make or sell has no price: not a price at the technique that would make
it if every technology were held. The sellers in reach are the home society's producers (a technique it
holds or can reach) and a trading partner that makes it, over a route. Everything here runs on small
fixtures; nothing builds a game or solves the whole tree."""

QUICK_TOPIC = True

import math
import types
import unittest
from unittest import mock

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine import foreign_capacity, material_availability, prices as engine_prices, solve_prices
from sim.engine.goods_market_offers import GoodsOffers, HOME_SELLER


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
        with mock.patch.object(engine_prices, "_unheld_steps_to", lambda node, held: steps[node]):
            goods, provenance = engine_prices.priced_goods_table(set(), _wage_document(), production_entries=entries)
        self.assertEqual(provenance["copper_kg"], "gated")
        self.assertNotIn("zinc_kg", goods)
        self.assertNotIn("zinc_kg", provenance)

    def test_every_label_left_is_a_seller_the_society_has_or_can_reach(self):
        entries = {"hand": _entry({"cloth_kg": 1.0}, labour_hours={"labourer": 1.0}),
                   "loom": _entry({"silk_kg": 1.0}, labour_hours={"labourer": 1.0}, requires_node="loom_node")}
        _goods, provenance = engine_prices.priced_goods_table(set(), _wage_document(), production_entries=entries)
        self.assertEqual(set(provenance.values()), {"solved", "gated"})


class _Route:
    cost_per_tonne = 10.0


def _fake_sim(home_prices, partner_makes, partner_prices, gated=(), supply=None, lift_in=math.inf):
    supply = supply or {}
    return types.SimpleNamespace(
        _price_tables=lambda: ({}, {material: ("gated" if material in gated else "solved")
                                    for material in home_prices}),
        foreign_supply_tonnes=lambda partner, material: supply.get(material, 1000.0),
        foreign_lift_left_tonnes=lambda partner, route: (lift_in, lift_in),
        _material_tag=lambda material: (material, material),
        _material_prices=lambda: home_prices,
        foreign_economies=lambda: ["partner"],
        state=types.SimpleNamespace(projects=types.SimpleNamespace(done=()),
                                    scenario=types.SimpleNamespace(year=100)),
        market_rate=lambda: 0.05,
        partner_price_level=lambda partner: 1.0,
        household=types.SimpleNamespace(),
        _foreign_economy_facts=lambda partner: {"solved_materials": frozenset(partner_makes),
                                                "prices_in_home_money": partner_prices},
        _trader_margin_share=lambda partner, route: 0.1,
        _cargo_lost_share=lambda route, material, partner: 0.0,
        _trader_cycle_years=lambda route, partner: 0.1,
        _agent_cost_per_tonne=lambda partner, route: 0.0,
        _material_price_per_kg=lambda material: home_prices.get(material),
    )


class _Offers(GoodsOffers):
    def __init__(self, sim, routes=None):
        self._sim = sim
        self.route = _Route() if routes is None else routes

    bought = 0.0

    def _route_from(self, civilization_id):
        return self.route

    def bought_tonnes(self, commodity, buyer_id=None):
        return self.bought


class SellerInReachTests(unittest.TestCase):

    def setUp(self):
        self.sim = _fake_sim(home_prices={"wheat_kg": 4.0}, partner_makes={"cassia_kg", "wheat_kg"},
                             partner_prices={"cassia_kg": 50.0, "wheat_kg": 1.0})

    def test_a_partner_that_makes_a_material_the_home_cannot_is_its_seller_at_the_landed_price(self):
        offers = _Offers(self.sim)
        landed = offers.landed_price("cassia_kg", "partner", offers.route)
        self.assertGreater(landed, 50.0)
        self.assertEqual(offers.offered_by("cassia_kg"), "partner")
        self.assertAlmostEqual(offers.household_prices()["cassia_kg"], landed)
        self.assertAlmostEqual(offers.unit_price("cassia_kg"), landed)

    def test_a_material_the_home_prices_keeps_its_home_seller_and_price(self):
        offers = _Offers(self.sim)
        self.assertEqual(offers.offered_by("wheat_kg"), HOME_SELLER)
        self.assertEqual(offers.household_prices()["wheat_kg"], 4.0)

    def test_a_material_no_one_in_reach_makes_has_no_seller_and_no_price(self):
        offers = _Offers(self.sim)
        self.assertIsNone(offers.offered_by("cobalt_kg"))
        self.assertIsNone(offers.unit_price("cobalt_kg"))
        self.assertFalse(offers.can_be_bought("cobalt_kg"))
        self.assertNotIn("cobalt_kg", offers.household_prices())

    def test_with_no_route_to_the_partner_its_material_is_unavailable(self):
        offers = _Offers(self.sim)
        offers.route = None
        self.assertIsNone(offers.offered_by("cassia_kg"))
        self.assertIsNone(offers.unit_price("cassia_kg"))

    def test_a_partner_that_will_not_let_it_cross_a_border_does_not_sell_it(self):
        with mock.patch("sim.engine.foreign_economies.not_traded_materials", lambda: frozenset({"cassia_kg"})):
            offers = _Offers(self.sim)
            self.assertIsNone(offers.offered_by("cassia_kg"))


class CheapestSellerInReachTests(unittest.TestCase):

    def _sim(self, **keywords):
        return _fake_sim(home_prices={"glass_kg": 40.0, "wheat_kg": 4.0}, partner_makes={"glass_kg", "wheat_kg"},
                         partner_prices={"glass_kg": 5.0, "wheat_kg": 1.0}, **keywords)

    def test_a_partner_that_sells_cheaper_than_a_technique_the_home_does_not_yet_run_is_the_seller(self):
        offers = _Offers(self._sim(gated={"glass_kg"}))
        self.assertEqual(offers.offered_by("glass_kg"), "partner")
        self.assertAlmostEqual(offers.unit_price("glass_kg"), offers.landed_price("glass_kg", "partner", offers.route))
        self.assertLess(offers.unit_price("glass_kg"), 40.0)

    def test_a_partner_that_sells_dearer_leaves_the_gated_home_technique_the_seller(self):
        sim = _fake_sim(home_prices={"glass_kg": 2.0}, partner_makes={"glass_kg"}, partner_prices={"glass_kg": 50.0},
                        gated={"glass_kg"})
        offers = _Offers(sim)
        self.assertEqual(offers.offered_by("glass_kg"), HOME_SELLER)
        self.assertEqual(offers.unit_price("glass_kg"), 2.0)

    def test_a_good_the_home_runs_a_producer_for_stays_with_the_home_even_where_a_partner_is_cheaper(self):
        offers = _Offers(self._sim(gated={"glass_kg"}))
        self.assertEqual(offers.offered_by("wheat_kg"), HOME_SELLER)
        self.assertEqual(offers.unit_price("wheat_kg"), 4.0)

    def test_a_partner_that_can_not_make_it_in_volume_is_no_seller(self):
        offers = _Offers(self._sim(gated={"glass_kg"}, supply={"glass_kg": 0.0}))
        self.assertEqual(offers.offered_by("glass_kg"), HOME_SELLER)


class ImportVolumeTests(unittest.TestCase):
    """What a partner brings is bounded by what it makes and the carriers' lift, not by the home output curves."""

    def _offers(self, supply, lift_in):
        sim = _fake_sim(home_prices={}, partner_makes={"cassia_kg"}, partner_prices={"cassia_kg": 50.0},
                        supply={"cassia_kg": supply}, lift_in=lift_in)
        return _Offers(sim)

    def test_the_smaller_of_the_partners_supply_and_the_lift_is_what_comes(self):
        self.assertEqual(self._offers(supply=30.0, lift_in=100.0).import_tonnes_available("cassia_kg"), 30.0)
        self.assertEqual(self._offers(supply=300.0, lift_in=100.0).import_tonnes_available("cassia_kg"), 100.0)

    def test_what_was_bought_this_year_comes_off_it(self):
        offers = self._offers(supply=300.0, lift_in=100.0)
        offers.bought = 40.0
        self.assertEqual(offers.import_tonnes_available("cassia_kg"), 60.0)
        offers.bought = 500.0
        self.assertEqual(offers.import_tonnes_available("cassia_kg"), 0.0)

    def test_a_good_the_home_sells_has_no_import_figure(self):
        sim = _fake_sim(home_prices={"wheat_kg": 4.0}, partner_makes=set(), partner_prices={})
        self.assertIsNone(_Offers(sim).import_tonnes_available("wheat_kg"))

    def test_a_route_with_no_lift_brings_nothing(self):
        self.assertEqual(self._offers(supply=300.0, lift_in=0.0).import_tonnes_available("cassia_kg"), 0.0)


class _Partner(foreign_capacity.ForeignCapacityMixin):
    DEFAULT_POPULATION_100AD = 100.0

    def __init__(self, can_make=True, opening=(0.0, 0.0), mined=False, book=None, curated=True, own_population=50.0):
        self.res = {"empire_output_100ad": {"ore_kg": 1.0} if curated else {}}
        self.civ = {"population": own_population}
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace(
            foreign_market_book={"partner": book or {}}))
        self._can_make, self._opening, self._mined = can_make, opening, mined

    def _foreign_economy_facts(self, civilization_id):
        return {"solved_materials": frozenset({"ore_kg"})}

    def _material_tag(self, material):
        return material, material

    def _foreign_can_make(self, civilization_id, material, solved):
        return self._can_make

    def foreign_opening(self, civilization_id, commodity, solved):
        return self._opening

    def _tracked_mineral(self, commodity):
        return self._mined

    def _national_output_tonnes(self, commodity):
        return 1000.0


class PartnerSupplyTests(unittest.TestCase):
    """A partner sells no more than it makes or holds."""

    def _supply(self, partner, material="ore_kg"):
        with mock.patch.object(foreign_capacity, "load_civ", lambda civilization_id: {"population": 10.0}):
            return partner.foreign_supply_tonnes("partner", material)

    def test_a_good_the_partner_cannot_make_supplies_nothing(self):
        self.assertEqual(self._supply(_Partner(can_make=False)), 0.0)
        self.assertEqual(self._supply(_Partner(), material="cobalt_kg"), 0.0)

    def test_an_opened_book_supplies_its_capacity_and_stock(self):
        book = {"ore_kg": {"capacity_tonnes": 7.0, "stock_tonnes": 3.0}}
        self.assertEqual(self._supply(_Partner(book=book)), 10.0)

    def test_the_opening_capacity_stands_before_the_book_opens(self):
        self.assertEqual(self._supply(_Partner(opening=(25.0, 40.0))), 25.0)

    def test_a_mined_good_with_no_deposit_in_its_regions_supplies_nothing(self):
        self.assertEqual(self._supply(_Partner(mined=True)), 0.0)

    def test_an_input_only_good_follows_the_partners_size_against_the_table_it_is_stated_for(self):
        self.assertAlmostEqual(self._supply(_Partner()), 1000.0 * 10.0 / 100.0 * foreign_capacity.FOREIGN_OUTPUT_PER_POPULATION_SHARE)

    def test_a_good_outside_the_reference_table_follows_this_societys_own_size(self):
        self.assertAlmostEqual(self._supply(_Partner(curated=False)), 1000.0 * 10.0 / 50.0 * foreign_capacity.FOREIGN_OUTPUT_PER_POPULATION_SHARE)


class ProjectNeedsASellerTests(unittest.TestCase):

    def _project(self, offers, stock_tonnes=0.0):
        node = {"mat": {"cobalt_kg": 100.0, "wheat_kg": 10.0}}
        game = types.SimpleNamespace(
            nodes={"alloy_works": node}, goods_market=offers,
            project_material_needs=lambda node_id: dict(node["mat"]),
            _material_tag=lambda material: (material, material),
            material_stock_t=lambda key: stock_tonnes)
        return game

    def test_a_project_needing_an_unsold_material_cannot_start_and_says_why(self):
        offers = _Offers(_fake_sim({"wheat_kg": 4.0}, set(), {}))
        game = self._project(offers)
        verdict = material_availability.check_materials_have_a_seller(game, "alloy_works", game.nodes["alloy_works"],
                                                                      False, None, True)
        self.assertFalse(verdict[0])
        self.assertIn("cobalt_kg", verdict[1])
        self.assertNotIn("wheat_kg", verdict[1])
        self.assertTrue(material_availability.check_materials_have_a_seller.blocker_kind == "supply")

    def test_the_boolean_answer_needs_no_sentence(self):
        offers = _Offers(_fake_sim({"wheat_kg": 4.0}, set(), {}))
        game = self._project(offers)
        verdict = material_availability.check_materials_have_a_seller(game, "alloy_works", game.nodes["alloy_works"],
                                                                      False, None, False)
        self.assertEqual(verdict, (False, None))

    def test_a_partner_that_sells_it_lets_the_project_start(self):
        offers = _Offers(_fake_sim({"wheat_kg": 4.0}, {"cobalt_kg"}, {"cobalt_kg": 20.0}))
        game = self._project(offers)
        self.assertIsNone(material_availability.check_materials_have_a_seller(
            game, "alloy_works", game.nodes["alloy_works"], False, None, True))

    def test_stock_already_held_needs_no_seller(self):
        offers = _Offers(_fake_sim({"wheat_kg": 4.0}, set(), {}))
        game = self._project(offers, stock_tonnes=math.inf)
        self.assertIsNone(material_availability.check_materials_have_a_seller(
            game, "alloy_works", game.nodes["alloy_works"], False, None, True))


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
        producers = solve_prices.build_producers_index(self.ENTRIES)
        resolvable = solve_prices.compute_resolvable_materials(self.ENTRIES, producers)
        self.assertIn("photovoltaic_panel_m2", resolvable)
        prices, iterations, residual, chosen = solve_prices.solve(
            self.ENTRIES, producers, resolvable, {"labourer": 1.0}, interest_rate=0.05)
        self.assertLess(residual, solve_prices.CONVERGENCE_TOLERANCE)
        self.assertLess(iterations, solve_prices.MAXIMUM_ITERATIONS // 10)
        self.assertEqual(chosen["electricity_generated_mj"], "photovoltaic")
        self.assertTrue(all(math.isfinite(price) and price > 0.0 for price in prices.values()))

    def test_without_the_panel_technique_the_dynamo_is_chosen(self):
        entries = {key: entry for key, entry in self.ENTRIES.items() if key != "photovoltaic"}
        producers = solve_prices.build_producers_index(entries)
        resolvable = solve_prices.compute_resolvable_materials(entries, producers)
        _prices, _iterations, _residual, chosen = solve_prices.solve(
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
