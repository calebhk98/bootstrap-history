"""Complaints/147: a project pays for the materials it is MISSING, at today's market price, and draws owned stock first.

A research node declares only quantities. The bill (`compute_material_bill`) takes what is held in stock, then what the
founder's own output covers over the build, and prices the rest at the market quote, the part beyond a year's market
supply at today's spot quote. It is called here on a stub game whose stock, output, supply and quotes are set by the test,
and `project_material_parts`, `project_own_output_claim`, `project_material_needs` and `bounty_price` on stubs too.
The wiring (starting a project, `why`, `quote material`) is test_complaint_147_bill_wiring."""
QUICK_TOPIC = True

import os
import types
import unittest

from sim.engine.project_materials import ProjectMaterialsMixin, compute_material_bill
from sim.ui.proto.techtree import _material_row

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_PRICE = 100.0     # money a tonne at the spot quote
CLIMB = 0.001          # fractional rise of the price per tonne already bought
TAGS = {"charcoal_kg": ("charcoal", "forest1"), "coal_kg": ("coal", "mine:coal"), "coke_kg": ("coal", "mine:coal"), "nitre_kg": ("saltpetre", "nitre"),
        "silver_g": ("silver", "mine:silver"), "tin_kg": ("tin", "mine:tin"), "ghost_kg": ("ghost", "mine:ghost")}


def a_view(stock=None, own=None, market=None, own_supply=None, unpriced=()):
    """A stub game: tonnes in stock by material, own output unclaimed a year by supply tag, market tonnes on offer a year."""
    stock, own, market = dict(stock or {}), dict(own or {}), dict(market or {})
    own_supply = dict(own_supply or own)

    def quote(material, tonnes, already=0.0):
        if material in unpriced:
            return None
        mean = BASE_PRICE * (1.0 + CLIMB * (already + tonnes / 2.0))
        return mean * tonnes, (mean if tonnes else BASE_PRICE * (1.0 + CLIMB * already))

    return types.SimpleNamespace(
        LAB_SCALE_SUFFIX="_g", _material_tag=lambda material: TAGS[material], material_stock_t=lambda emp_key: stock.get(emp_key, 0.0),
        _unclaimed_own_supply=lambda tag, node_id: own.get(tag, 0.0), _own_material_supply=lambda tag: own_supply.get(tag, 0.0),
        _material_market_tonnes=lambda emp_key: market.get(emp_key, 1000.0), material_purchase_cost=quote)


def bill(view, needs, span=1.0):
    return compute_material_bill(view, "node", needs, span)


def row_of(result, material):
    return next(row for row in result["rows"] if row["material"] == material)


class StockFirst(unittest.TestCase):
    def test_holding_a_material_covers_it_and_takes_its_cost_off_the_bill(self):
        held = row_of(bill(a_view(stock={"charcoal": 5000.0}), {"charcoal_kg": 2000.0}), "charcoal_kg")
        bare = row_of(bill(a_view(), {"charcoal_kg": 2000.0}), "charcoal_kg")
        self.assertEqual(held["missing_tonnes"], 0.0)
        self.assertAlmostEqual(held["held_from_stock_tonnes"], held["needed_tonnes"])
        self.assertEqual(held["cost_of_missing"], 0.0)
        self.assertGreater(bare["cost_of_missing"], 0.0)

    def test_with_nothing_held_every_needed_tonne_is_missing(self):
        row = row_of(bill(a_view(), {"charcoal_kg": 2000.0}), "charcoal_kg")
        self.assertAlmostEqual(row["missing_tonnes"], row["needed_tonnes"])
        self.assertEqual(row["held_tonnes"], 0.0)

    def test_stock_is_drawn_once_across_materials_sharing_a_stock(self):
        result = bill(a_view(stock={"charcoal": 3.0}), {"charcoal_kg": 2000.0, "coal_kg": 2000.0})
        self.assertAlmostEqual(row_of(result, "charcoal_kg")["held_from_stock_tonnes"], 2.0)
        self.assertEqual(row_of(result, "coal_kg")["held_from_stock_tonnes"], 0.0)


class OwnOutput(unittest.TestCase):
    def test_own_output_over_the_build_covers_what_stock_does_not(self):
        row = row_of(bill(a_view(own={"forest1": 1.0}), {"charcoal_kg": 4000.0}, span=3.0), "charcoal_kg")   # 4 t needed, 3 t of output
        self.assertAlmostEqual(row["held_from_own_output_tonnes"], 3.0)
        self.assertAlmostEqual(row["missing_tonnes"], 1.0)

    def test_owned_supply_lowers_the_bill_and_is_named_on_the_why_row(self):
        bare = row_of(bill(a_view(), {"charcoal_kg": 4000.0}), "charcoal_kg")
        owner_view = a_view(own={"forest1": 2.0})
        owner = row_of(bill(owner_view, {"charcoal_kg": 4000.0}), "charcoal_kg")
        self.assertGreater(owner["held_from_own_output_tonnes"], 0.0)
        self.assertLess(owner["missing_tonnes"], bare["missing_tonnes"])
        self.assertLess(owner["cost_of_missing"], bare["cost_of_missing"])
        self.assertLessEqual(owner["price_per_tonne"], bare["price_per_tonne"] * (1.0 + 1e-9))
        shown = _material_row(owner, owner_view)
        self.assertGreater(shown["own_supply_tonnes_per_year"], 0)
        # presentation: the why row names the owned supply
        self.assertIn("own", shown["scarcity_note"])
        self.assertIn("charcoal_kg", shown["scarcity_note"])

    def test_without_owned_supply_the_why_row_carries_no_note(self):
        bare = row_of(bill(a_view(), {"charcoal_kg": 4000.0}), "charcoal_kg")
        shown = _material_row(bare, a_view())
        self.assertEqual(shown["own_supply_tonnes_per_year"], 0)
        self.assertNotIn("scarcity_note", shown)

    def test_a_project_claims_the_output_it_draws_so_the_next_counts_only_what_is_left(self):
        game = types.SimpleNamespace(
            nodes={"first": {"build_yrs": 4}},
            project_material_bill=lambda node_id: {"rows": [
                {"material": "charcoal_kg", "held_from_own_output_tonnes": 8.0},
                {"material": "coal_kg", "held_from_own_output_tonnes": 0.0}]},
            _material_tag=lambda material: TAGS[material])
        self.assertEqual(ProjectMaterialsMixin.project_own_output_claim(game, "first"), {"forest1": 2.0})

    def test_the_unclaimed_supply_is_the_output_less_what_other_running_projects_claimed(self):
        active = {"first": {"own_output_claim": {"forest1": 2.0}}, "second": {"own_output_claim": {"forest1": 0.5}},
                  "third": {}}
        game = types.SimpleNamespace(state=types.SimpleNamespace(projects=types.SimpleNamespace(active=active)),
                                     _own_material_supply=lambda tag: 3.0)
        self.assertAlmostEqual(ProjectMaterialsMixin._unclaimed_own_supply(game, "forest1", "third"), 0.5)
        self.assertAlmostEqual(ProjectMaterialsMixin._unclaimed_own_supply(game, "forest1", "first"), 2.5)
        game._own_material_supply = lambda tag: 2.0   # the others claimed more than there is
        self.assertEqual(ProjectMaterialsMixin._unclaimed_own_supply(game, "forest1", "third"), 0.0)


class MarketPrice(unittest.TestCase):
    def test_the_missing_part_is_priced_at_the_market_quote(self):
        view = a_view()
        row = row_of(bill(view, {"coal_kg": 2000.0}), "coal_kg")
        self.assertAlmostEqual(row["cost_of_missing"], view.material_purchase_cost("coal_kg", 2.0)[0])
        self.assertTrue(row["priced"])

    def test_a_larger_order_pays_more_a_tonne(self):
        small = row_of(bill(a_view(), {"coal_kg": 2000.0}), "coal_kg")
        large = row_of(bill(a_view(), {"coal_kg": 400000.0}), "coal_kg")
        self.assertGreater(large["price_per_tonne"], small["price_per_tonne"])

    def test_the_total_of_the_rows_is_the_cost_of_the_missing_part(self):
        result = bill(a_view(), {"coal_kg": 2000.0, "charcoal_kg": 3000.0, "tin_kg": 1000.0})
        self.assertAlmostEqual(sum(row["cost_of_missing"] for row in result["rows"]), result["cost_of_missing"])
        self.assertEqual(len(result["rows"]), 3)

    def test_a_material_no_one_sells_has_no_price_and_costs_nothing_in_the_bill(self):
        row = row_of(bill(a_view(unpriced=("ghost_kg",)), {"ghost_kg": 1000.0}), "ghost_kg")
        self.assertFalse(row["priced"])
        self.assertEqual(row["cost_of_missing"], 0.0)
        self.assertGreater(row["missing_tonnes"], 0.0)


class InstalmentsBeyondAYearsSupply(unittest.TestCase):
    """The part beyond a year's market supply is bought over the following years at today's spot quote."""

    def setUp(self):
        self.view = a_view(market={"saltpetre": 10.0})
        self.row = row_of(bill(self.view, {"nitre_kg": 30000.0}), "nitre_kg")   # 30 t needed, 10 t on offer a year

    def test_only_a_years_supply_is_deliverable_now(self):
        self.assertAlmostEqual(self.row["missing_tonnes"], 30.0)
        self.assertAlmostEqual(self.row["deliverable_now_tonnes"], 10.0)

    def test_the_part_beyond_costs_the_spot_quote(self):
        spot = self.view.material_purchase_cost("nitre_kg", 0.0)[1]
        self.assertAlmostEqual(self.row["cost_of_missing"] - self.row["cost_of_deliverable"], 20.0 * spot)

    def test_buying_the_whole_order_at_once_would_climb_further(self):
        whole_order = self.view.material_purchase_cost("nitre_kg", 30.0)[0]
        self.assertLess(self.row["cost_of_missing"], whole_order)

    def test_up_front_money_is_the_deliverable_part_only(self):
        game = types.SimpleNamespace(project_material_bill=lambda node_id: {"rows": [self.row], "cost_of_missing": self.row["cost_of_missing"]})
        total, up_front = ProjectMaterialsMixin.project_material_parts(game, "node")
        self.assertAlmostEqual(up_front, self.row["cost_of_deliverable"])
        self.assertLess(up_front, total)

    def test_materials_drawing_on_one_supply_share_its_year(self):
        both = bill(a_view(market={"coal": 10.0}), {"coal_kg": 8000.0, "coke_kg": 8000.0})   # 10 t a year between two keys
        self.assertAlmostEqual(row_of(both, "coal_kg")["deliverable_now_tonnes"], 8.0)
        self.assertAlmostEqual(row_of(both, "coke_kg")["deliverable_now_tonnes"], 2.0)

    def test_a_laboratory_scale_material_is_all_deliverable(self):
        row = row_of(bill(a_view(market={"silver": 0.0}), {"silver_g": 5000.0}), "silver_g")
        self.assertAlmostEqual(row["deliverable_now_tonnes"], row["missing_tonnes"])
        self.assertIsNone(row["years_of_supply_it_takes"])


class Needs(unittest.TestCase):
    def game(self, fuel):
        return types.SimpleNamespace(nodes={"node": {"mat": {"charcoal_kg": 100.0, "tin_kg": 5.0}}}, chosen_fuel=lambda node_id: fuel,
                                     COKE_PER_CHARCOAL=0.5)

    def test_a_project_needs_what_its_node_declares(self):
        self.assertEqual(dict(ProjectMaterialsMixin.project_material_needs(self.game("charcoal"), "node")),
                         {"charcoal_kg": 100.0, "tin_kg": 5.0})

    def test_with_coke_chosen_coal_stands_in_for_the_charcoal(self):
        self.assertEqual(dict(ProjectMaterialsMixin.project_material_needs(self.game("coke"), "node")),
                         {"coal_kg": 50.0, "tin_kg": 5.0})


class BountyAndSource(unittest.TestCase):
    def test_a_bounty_is_a_multiple_of_what_this_society_would_pay_to_build_it(self):
        game = types.SimpleNamespace(project_cost_now=lambda node_id: 900.0, opposition_factor=lambda node_id: 1.5,
                                     BOUNTY_PRICE_MULTIPLIER=4.0)
        self.assertAlmostEqual(ProjectMaterialsMixin.bounty_price(game, "node"), 900.0 / 1.5 * 4.0)

    def test_no_reader_of_prices_json_in_the_project_materials_module(self):
        with open(os.path.join(ROOT, "sim", "engine", "project_materials.py"), encoding="utf-8") as source:
            text = source.read()
        self.assertNotIn("prices.json", text)
        self.assertNotIn("PRICES", text)


if __name__ == "__main__":
    unittest.main()
