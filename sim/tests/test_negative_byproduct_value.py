"""Complaints/309: a glutted waste by-product prices at minus its disposal cost, and the batch is still recovered."""

QUICK_TOPIC = True

import math
import unittest

from sim.engine import disposal_cost, joint_allocation, joint_floor, solve_prices, solve_prices_core
from sim.world import demand, need_demand

OUTPUTS = {"tar_kg": 1000.0, "charcoal_kg": 2500.0}
BATCH_COST = 760.0
TAR_DISPOSAL_COST_PER_UNIT = 0.005
TAR = frozenset({"tar_kg"})


def allocate(tar_anchor, tar_disposal_cost, glutted=TAR):
    return joint_allocation.allocate_joint_cost(
        OUTPUTS, {}, BATCH_COST, {"tar_kg": tar_anchor, "charcoal_kg": 4.0},
        disposal_cost_by_material={"tar_kg": tar_disposal_cost}, glutted_materials=glutted)


class GlutPriceTests(unittest.TestCase):

    def test_a_glutted_byproduct_prices_at_minus_its_disposal_cost(self):
        prices = allocate(1e-9, TAR_DISPOSAL_COST_PER_UNIT)
        self.assertAlmostEqual(prices["tar_kg"], -TAR_DISPOSAL_COST_PER_UNIT)

    def test_a_low_anchor_is_not_a_glut_unless_the_clearing_search_says_so(self):
        prices = allocate(1e-9, TAR_DISPOSAL_COST_PER_UNIT, glutted=frozenset())
        self.assertGreaterEqual(prices["tar_kg"], 0.0)

    def test_the_batch_is_recovered_and_the_main_product_pays_the_disposal(self):
        prices = allocate(1e-9, TAR_DISPOSAL_COST_PER_UNIT)
        free = allocate(1e-9, 0.0)
        recovered = sum(prices[name] * quantity for name, quantity in OUTPUTS.items())
        self.assertAlmostEqual(recovered, BATCH_COST)
        self.assertGreater(prices["charcoal_kg"], free["charcoal_kg"])

    def test_a_byproduct_with_demand_above_its_disposal_cost_keeps_a_positive_price(self):
        prices = allocate(0.5, TAR_DISPOSAL_COST_PER_UNIT, glutted=frozenset())
        self.assertGreater(prices["tar_kg"], 0.0)

    def test_an_unanchored_output_is_never_priced_below_zero(self):
        prices = joint_allocation.allocate_joint_cost(
            OUTPUTS, {}, BATCH_COST, {}, disposal_cost_by_material={"tar_kg": TAR_DISPOSAL_COST_PER_UNIT})
        self.assertGreaterEqual(prices["tar_kg"], 0.0)

    def test_a_negative_reference_value_does_not_corrupt_the_split(self):
        shares = joint_allocation._split_by_value(OUTPUTS, {"tar_kg": -3.0, "charcoal_kg": 4.0}, BATCH_COST)
        self.assertTrue(all(price >= 0.0 for price in shares.values()))
        self.assertAlmostEqual(sum(shares[name] * OUTPUTS[name] for name in OUTPUTS), BATCH_COST)

    def test_the_bound_lifts_a_price_below_it_and_charges_the_others(self):
        prices = {"tar_kg": -1.0, "charcoal_kg": 0.5}
        lifted = joint_floor.bound_to_disposal_cost(prices, OUTPUTS, {"tar_kg": 0.002})
        self.assertAlmostEqual(lifted["tar_kg"], -0.002)
        self.assertAlmostEqual(
            sum(lifted[name] * OUTPUTS[name] for name in OUTPUTS),
            sum(prices[name] * OUTPUTS[name] for name in OUTPUTS))


GEM_NEEDS = {"needs": {"ornament": {"surplus_budget_share": 1.0}},
             "goods": {"gem_kg": {"satisfies": {"ornament": 1.0}}}}
GEM_SMELT = {"outputs": {"metal_kg": 10.0, "gem_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 5.0}}


class ClearingSearchGlutTests(unittest.TestCase):
    """A glut is the clearing search finding supply above demand at every price it tries."""

    def anchors(self, supply_kg, table_supply=()):
        model = need_demand.NeedDemandModel(
            GEM_NEEDS, {"smelt": GEM_SMELT}, demand.income_bins(1_000_000.0, 500.0))
        return need_demand.NeedDemandAnchors(model, {"gem_kg": supply_kg}, table_supply)

    def test_supply_beyond_demand_at_every_price_is_a_glut(self):
        self.assertEqual(self.anchors(1e30).glutted_materials({"gem_kg": 1.0}), {"gem_kg"})

    def test_scarce_supply_is_not_a_glut(self):
        self.assertEqual(self.anchors(10.0).glutted_materials({"gem_kg": 1.0}), set())

    def test_a_market_clearing_below_the_disposal_cost_is_a_glut(self):
        anchors = self.anchors(10.0)
        clearing = anchors.prices({"gem_kg": 1.0})["gem_kg"]
        self.assertEqual(anchors.glutted_materials({"gem_kg": 1.0}, {"gem_kg": clearing * 10.0}), {"gem_kg"})
        self.assertEqual(anchors.glutted_materials({"gem_kg": 1.0}, {"gem_kg": clearing / 10.0}), set())

    def test_a_decayed_price_does_not_hide_a_market_that_clears_above_the_disposal_cost(self):
        anchors = self.anchors(10.0)
        clearing = anchors.prices({"gem_kg": 1.0})["gem_kg"]
        self.assertEqual(anchors.glutted_materials({"gem_kg": clearing * 1e-12}, {"gem_kg": clearing / 10.0}), set())

    def test_a_table_supplied_good_is_never_reported_as_glut(self):
        self.assertEqual(self.anchors(1e30, ("gem_kg",)).glutted_materials({"gem_kg": 1.0}), set())


class DisposalCostTests(unittest.TestCase):

    def test_it_grows_with_distance_to_the_dump(self):
        near = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 0.0, distance_kilometres=1.0)
        far = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 0.0, distance_kilometres=10.0)
        self.assertGreater(far, near)

    def test_it_grows_with_the_price_of_ground(self):
        cheap = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 0.01)
        dear = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 1.0)
        self.assertGreater(dear, cheap)

    def test_it_falls_with_bulk_density_and_heap_height(self):
        loose = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 1.0, bulk_density=500.0)
        dense = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 1.0, bulk_density=2000.0)
        low = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 1.0, heap_height=1.0)
        high = disposal_cost.disposal_cost_hours_per_kilogram(1.0, 0.5, 1.0, heap_height=6.0)
        self.assertGreater(loose, dense)
        self.assertGreater(low, high)

    def test_land_is_capitalised_at_the_interest_rate(self):
        patient = disposal_cost.disposal_cost_hours_per_kilogram(0.0, 0.0, 1.0, interest_rate=0.02)
        impatient = disposal_cost.disposal_cost_hours_per_kilogram(0.0, 0.0, 1.0, interest_rate=0.2)
        self.assertGreater(patient, impatient)

    def test_only_joint_outputs_get_a_bound(self):
        entries = {"kiln": {"outputs": {"tar_kg": 1.0, "charcoal_kg": 2.0}},
                   "mill": {"outputs": {"flour_kg": 1.0}}}
        self.assertEqual(disposal_cost.joint_output_materials(entries), ["charcoal_kg", "tar_kg"])


SERVICE_PRICES = {"waste_handling_job": 1.0, "waste_haulage_tkm": 0.3, "dump_ground_m2": 0.01}


class MaterialDisposalCostTests(unittest.TestCase):
    """The cost per unit of a material from the sink services' solved prices and the material's heap."""

    def cost(self, material, prices=None, **terms):
        return disposal_cost.disposal_cost_by_material(
            [material], SERVICE_PRICES if prices is None else prices, 0.05, **terms)[material]

    def test_without_the_sink_services_disposal_is_free(self):
        self.assertEqual(disposal_cost.disposal_cost_by_material(["tar_kg"], {}, 0.05), {})
        self.assertEqual(disposal_cost.disposal_price_floor(["tar_kg"], {}, 0.05), {})

    def test_the_cost_is_the_services_at_the_materials_own_heap(self):
        density, height = disposal_cost.heap_of("basic_slag_kg")
        kilograms_per_tonne = 1000.0
        years = 1.0 / 0.05
        expected = (SERVICE_PRICES["waste_handling_job"]
                    + SERVICE_PRICES["waste_haulage_tkm"] * disposal_cost.DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES
                    + SERVICE_PRICES["dump_ground_m2"] * years * kilograms_per_tonne / (density * height)
                    ) / kilograms_per_tonne
        self.assertAlmostEqual(self.cost("basic_slag_kg"), expected)

    def test_a_denser_material_covers_less_ground(self):
        slag_density, slag_height = disposal_cost.heap_of("basic_slag_kg")
        ash_density, ash_height = disposal_cost.heap_of("wood_ash_kg")
        self.assertGreater(slag_density * slag_height, ash_density * ash_height)
        ground_only = dict(SERVICE_PRICES, waste_handling_job=0.0, waste_haulage_tkm=0.0)
        self.assertLess(self.cost("basic_slag_kg", ground_only), self.cost("wood_ash_kg", ground_only))

    def test_a_material_with_no_entry_takes_the_default_heap(self):
        self.assertEqual(disposal_cost.heap_of("never_heard_of_it_kg"), disposal_cost.default_heap())

    def test_the_cost_is_per_unit_of_the_material(self):
        costs = disposal_cost.disposal_cost_by_material(["wood_tar_kg", "gold_g"], SERVICE_PRICES, 0.05)
        self.assertGreater(costs["wood_tar_kg"], costs["gold_g"] * 100.0)

    def test_the_state_rule_sets_the_dump_distance_only_when_it_is_the_longer(self):
        free = disposal_cost.DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES
        self.assertAlmostEqual(self.cost("tar_kg", minimum_dump_distance_kilometres=0.0), self.cost("tar_kg"))
        self.assertAlmostEqual(self.cost("tar_kg", minimum_dump_distance_kilometres=free / 2.0), self.cost("tar_kg"))
        self.assertGreater(self.cost("tar_kg", minimum_dump_distance_kilometres=free * 5.0), self.cost("tar_kg"))

    def test_a_civilisations_rule_is_read_from_its_record_and_defaults_to_none(self):
        from sim.engine import prices as price_engine
        self.assertEqual(price_engine.waste_dump_minimum_distance({"id": "anywhere"}), 0.0)
        self.assertEqual(price_engine.waste_dump_minimum_distance(None), 0.0)
        record = {"id": "anywhere", "waste_dump_minimum_distance_kilometres": 7.5}
        self.assertEqual(price_engine.waste_dump_minimum_distance(record), 7.5)
        self.assertNotEqual(price_engine.territory_fingerprint(record),
                            price_engine.territory_fingerprint({"id": "anywhere"}))


class SolverTests(unittest.TestCase):

    def test_a_negative_price_still_moving_is_not_converged(self):
        prices, residual = solve_prices_core._solve_round_update_prices(
            ["waste_kg"], {"waste_kg": -0.1}, {"waste_kg": [(-0.5, "dump")]}, 0.5, {})
        self.assertAlmostEqual(prices["waste_kg"], -0.3)
        self.assertGreater(residual, 0.1)

    def test_the_bound_applies_before_the_cheapest_candidate_is_chosen(self):
        prices, _residual = solve_prices_core._solve_round_update_prices(
            ["waste_kg"], {"waste_kg": 0.0}, {"waste_kg": [(-5.0, "glut"), (1.0, "other")]}, 1.0, {},
            disposal_floor={"waste_kg": -0.25})
        self.assertAlmostEqual(prices["waste_kg"], -0.25)


def real_sink_entries():
    production = demand.production_data()
    entries = {key: production[key] for key in production
               if production[key].get("service") and key in disposal_cost_entry_keys()}
    entries["hectare_land"] = {"outputs": {"hectare_land": 1.0}, "inputs": {}, "labour_hours": {}}
    return entries


def disposal_cost_entry_keys():
    return {"waste_handling_job", "waste_haulage_on_foot", "waste_haulage_by_pack_animal",
            "waste_haulage_by_cart", "dump_ground_m2"}


class GluttedDemand:
    glutted = frozenset({"tar_kg"})

    def prices(self, _prices):
        return {"tar_kg": 1e-12, "charcoal_kg": 2.0}

    def glutted_materials(self, _prices, _disposal_costs=None):
        return self.glutted


KILN = {"kiln": {"outputs": {"tar_kg": 1000.0, "charcoal_kg": 2500.0}, "inputs": {},
                 "labour_hours": {"labourer": 100.0}}}


def solve_kiln(sink=True, rule=0.0, gate=None, demand_anchors=None):
    entries = dict(KILN)
    if sink:
        entries.update({key: value for key, value in real_sink_entries().items()
                        if gate is None or value.get("requires_node") in (None, *gate)})
    producers = solve_prices.build_producers_index(entries)
    resolvable = solve_prices.compute_resolvable_materials(
        entries, producers, rent_hours_per_kg_by_material={"hectare_land": 40.0})
    prices, _i, _r, chosen = solve_prices.solve(
        entries, producers, resolvable, {"labourer": 1.0},
        rent_hours_per_kg_by_material={"hectare_land": 40.0}, interest_rate=0.05,
        demand_anchors=demand_anchors or GluttedDemand(), dump_minimum_distance_kilometres=rule)
    return prices, resolvable, chosen


class SinkRecipeSolveTests(unittest.TestCase):
    """The disposal sink is data, priced by the cost routine; the glut sets the price at minus its cost."""

    def test_the_sink_services_are_reachable_ordinary_materials(self):
        _prices, resolvable, chosen = solve_kiln()
        for material in ("waste_handling_job", "waste_haulage_tkm", "dump_ground_m2"):
            self.assertIn(material, resolvable)
            self.assertIn(material, chosen)

    def test_the_cheapest_haulage_available_sets_its_price(self):
        both, _r, chosen_both = solve_kiln()
        foot_only, _r2, chosen_foot = solve_kiln(gate=())
        self.assertEqual(chosen_both["waste_haulage_tkm"], "waste_haulage_by_cart")
        self.assertEqual(chosen_foot["waste_haulage_tkm"], "waste_haulage_on_foot")
        self.assertLess(both["waste_haulage_tkm"], foot_only["waste_haulage_tkm"])

    def test_a_solved_glut_prices_at_minus_the_disposal_cost_and_the_batch_is_recovered(self):
        prices, _r, _c = solve_kiln()
        expected = disposal_cost.disposal_cost_by_material(["tar_kg"], prices, 0.05)["tar_kg"]
        self.assertGreater(expected, 0.0)
        self.assertLess(prices["tar_kg"], 0.0)
        self.assertAlmostEqual(prices["tar_kg"], -expected, places=9)
        self.assertAlmostEqual(prices["tar_kg"] * 1000.0 + prices["charcoal_kg"] * 2500.0, 100.0, places=4)

    def test_a_longer_dump_distance_rule_makes_the_waste_dearer_to_get_rid_of(self):
        free, _r, _c = solve_kiln(rule=0.0)
        ruled, _r2, _c2 = solve_kiln(rule=50.0)
        self.assertLess(ruled["tar_kg"], free["tar_kg"])
        self.assertGreater(ruled["charcoal_kg"], free["charcoal_kg"])

    def test_with_no_sink_in_the_solve_a_glut_is_free_to_dump(self):
        prices, _r, _c = solve_kiln(sink=False)
        self.assertAlmostEqual(prices["tar_kg"], 0.0, places=9)
        self.assertAlmostEqual(prices["charcoal_kg"] * 2500.0, 100.0, places=4)

    def test_the_search_not_a_share_of_the_cost_decides_a_glut(self):
        class NoGlut(GluttedDemand):
            glutted = frozenset()
        prices, _r, _c = solve_kiln(demand_anchors=NoGlut())
        self.assertGreaterEqual(prices["tar_kg"], 0.0)

    def test_the_solved_prices_stay_finite(self):
        prices, _r, _c = solve_kiln()
        self.assertTrue(all(math.isfinite(price) for price in prices.values()))


class WasteConsumerTests(unittest.TestCase):
    """A recipe that takes a waste is credited what it saves the waste's maker, never more."""

    ENTRY = {"outputs": {"cement_kg": 1.0}, "inputs": {"slag_kg": 10.0}, "labour_hours": {"labourer": 5.0}}

    def cost(self, slag_price, slag_disposal_cost, labour=5.0):
        entry = dict(self.ENTRY, labour_hours={"labourer": labour})
        disposal = solve_prices_core.Disposal(costs={"slag_kg": slag_disposal_cost})
        total, prices = solve_prices_core.recipe_cost_and_allocation(
            "cement", entry, {"slag_kg": slag_price}, {"labourer": 1.0}, disposal=disposal)
        return total, prices["cement_kg"]

    def test_the_credit_is_the_avoided_disposal_cost(self):
        total, _price = self.cost(-0.2, 0.2)
        self.assertAlmostEqual(total, 5.0 - 2.0)

    def test_a_price_below_the_disposal_cost_earns_no_more_than_the_cost(self):
        total, _price = self.cost(-50.0, 0.2)
        self.assertAlmostEqual(total, 5.0 - 2.0)

    def test_a_credit_cannot_make_the_product_cost_less_than_nothing(self):
        total, price = self.cost(-0.2, 0.2, labour=0.5)
        self.assertEqual(total, 0.0)
        self.assertEqual(price, 0.0)

    def test_a_positively_priced_input_is_charged_in_full(self):
        total, _price = self.cost(3.0, 0.2)
        self.assertAlmostEqual(total, 5.0 + 30.0)


if __name__ == "__main__":
    unittest.main()
