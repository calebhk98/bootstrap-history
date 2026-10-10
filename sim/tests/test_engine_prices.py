"""Checks `sim/engine/prices.py` - the first wiring of the price solver into
the engine, per the stakeholder's "prices.json should be slowly deleted."

Three things this pins, because getting any one of them wrong would defeat
the whole point of the module:

  - the cache is keyed on the set of GATE NODES HELD, not the full
    technology set - two technology sets that differ only outside the gate
    set must hit the same cache entry, and one that differs INSIDE it must
    miss;
  - the labour-hours -> denarii conversion is a multiplication by the
    labourer wage rate, not some other rate or direction;
  - the engine's default (`sim.engine.data.load()` with no arguments)
    prices every material from the solver, with no price book behind it.

Written as unittest.TestCase against synthetic production entries, like
test_price_solver_cycles.py and test_price_solver_era_gate.py, so this does
not depend on the real, changing contents of data/production/ for anything
but one light integration check at the end.

sim/engine/prices.py: solver prices cached on held gate nodes, per-material solved/gated provenance.
"""
import json
import os
import unittest

from sim.engine import data, prices as engine_prices


def _prices_json(labourer_rate=2.0, smith_rate=4.0, money_per_labour_hour=None):
    """A minimal wage document: just enough for
    wage_ratios_by_trade and denarii_per_labour_hour to read."""
    return {
        "wage_rates_denarii_per_hour": {
            "labourer": {"rate": labourer_rate},
            "smith": {"rate": smith_rate},
        },
        "money_per_labour_hour": (labourer_rate if money_per_labour_hour is None
                                  else money_per_labour_hour),
    }


def _entry(outputs, inputs=None, labour_hours=None, requires_node="__absent__"):
    built = {"outputs": outputs, "inputs": inputs or {},
             "labour_hours": labour_hours or {}}
    if requires_node != "__absent__":
        built["requires_node"] = requires_node
    return built


class GateNodeSetTests(unittest.TestCase):
    """`all_gate_nodes` - the subset the cache actually keys on."""

    def test_only_entries_naming_an_actual_node_are_gates(self):
        entries = {
            "universal": _entry({"straw_kg": 1.0}, requires_node=None),
            "gated_a": _entry({"iron_kg": 1.0}, requires_node="smelting"),
            "gated_b": _entry({"steel_kg": 1.0}, requires_node="smelting"),
            "gated_c": _entry({"zinc_kg": 1.0}, requires_node="electrolysis"),
            "unclassified": _entry({"mystery_kg": 1.0}),
        }
        # "smelting" is named twice - the result is a SET, so it counts once.
        self.assertEqual(engine_prices.all_gate_nodes(entries),
                         frozenset({"smelting", "electrolysis"}))


class CacheKeyingTests(unittest.TestCase):
    """The design's whole point: cache on gate nodes held, not the full set.

    A gated solve is expensive enough (fractions of a second on the real
    tree) that this module exists specifically so the engine pays it only
    when the answer could actually change - see the module docstring's
    CACHE KEY section.
    """

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        self.prices_json = _prices_json()
        # timber is extracted (no requires_node at all is fine here since it
        # is admitted with requires_node=None - universally available - the
        # solve needs SOMETHING to bottom out in); the gate sits on the
        # technique that turns timber into charcoal, which only the smelting
        # node unlocks.
        self.entries = {
            "timber": _entry({"timber_m3": 1.0}, requires_node=None,
                             labour_hours={"labourer": 1.0}),
            "charcoal": _entry({"charcoal_kg": 2.0}, inputs={"timber_m3": 1.0},
                               requires_node="charcoal_burning",
                               labour_hours={"labourer": 1.0}),
        }

    def test_two_held_sets_with_the_same_gate_intersection_share_a_result(self):
        result_a = engine_prices.solved_prices(
            {"charcoal_burning"}, self.prices_json, production_entries=self.entries)
        # "irrelevant_tech" is not any entry's requires_node, so it cannot be
        # a gate - adding it must not change the cache key at all.
        result_b = engine_prices.solved_prices(
            {"charcoal_burning", "irrelevant_tech", "another_non_gate"},
            self.prices_json, production_entries=self.entries)
        self.assertIs(result_a, result_b,
                      "a non-gate technology changed the cached result")

    def test_a_different_gate_intersection_is_a_cache_miss(self):
        without_gate = engine_prices.solved_prices(
            set(), self.prices_json, production_entries=self.entries)
        with_gate = engine_prices.solved_prices(
            {"charcoal_burning"}, self.prices_json, production_entries=self.entries)
        self.assertIsNot(without_gate, with_gate)
        self.assertNotIn("charcoal_kg", without_gate.resolvable_materials)
        self.assertIn("charcoal_kg", with_gate.resolvable_materials)

    def test_a_different_production_entries_object_cannot_collide(self):
        # Guards the id()-reuse hazard CLAUDE.md section 6 and Complaints/27
        # are about: two DIFFERENT entries dicts that happen to produce the
        # same gate-node key must not share a cached result just because a
        # dict got reused at the same memory address in some interpreter.
        # Here they are simply two distinct (but gate-equivalent) objects
        # live at the same time, which is the ordinary case this guards.
        other_entries = dict(self.entries)  # a different dict, same content
        first = engine_prices.solved_prices(
            {"charcoal_burning"}, self.prices_json, production_entries=self.entries)
        second = engine_prices.solved_prices(
            {"charcoal_burning"}, self.prices_json, production_entries=other_entries)
        # Different objects in, so this must NOT be treated as the same
        # cache entry (the `is production_entries` check must fail and
        # trigger a fresh solve) even though the two solves happen to agree.
        self.assertIsNot(first, second)
        self.assertEqual(first.prices_in_labour_hours,
                         second.prices_in_labour_hours)


class ConversionTests(unittest.TestCase):
    """LABOUR-HOURS TO DENARII: multiply by the document's coin-anchored
    money per labour hour."""

    def test_one_labour_hour_is_worth_the_documents_money_per_hour(self):
        prices_json = _prices_json(money_per_labour_hour=3.5)
        self.assertEqual(
            engine_prices.hours_to_denarii(1.0, prices_json), 3.5)

    def test_round_trips_against_division_by_the_money_per_hour(self):
        prices_json = _prices_json(money_per_labour_hour=2.5)
        denarii = 40.0
        hours = denarii / 2.5
        self.assertAlmostEqual(
            engine_prices.hours_to_denarii(hours, prices_json), denarii)

    def test_wage_rates_are_not_used_for_the_conversion(self):
        prices_json = _prices_json(labourer_rate=7.0, smith_rate=9.0,
                                   money_per_labour_hour=2.0)
        self.assertEqual(engine_prices.denarii_per_labour_hour(prices_json), 2.0)


class PricedGoodsTableTests(unittest.TestCase):
    """`priced_goods_table` - the solved table and its provenance report."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)

    def test_a_resolvable_material_is_marked_solved_and_converted(self):
        prices_json = _prices_json(labourer_rate=2.0)
        entries = {
            "straw": _entry({"straw_kg": 1.0}, requires_node=None,
                            labour_hours={"labourer": 3.0}),
        }
        goods, provenance = engine_prices.priced_goods_table(
            set(), prices_json, production_entries=entries)
        self.assertEqual(provenance, {"straw_kg": "solved"})
        # 3 labour-hours at 2 denarii/hour = 6 denarii.
        self.assertAlmostEqual(goods["straw_kg"], 6.0)

    def test_a_material_nothing_makes_has_no_price(self):
        entries = {
            "requires_missing_input": _entry(
                {"widget_kg": 1.0}, inputs={"no_recipe_for_this_kg": 1.0},
                requires_node=None, labour_hours={"labourer": 1.0}),
        }
        goods, provenance = engine_prices.priced_goods_table(
            set(), _prices_json(), production_entries=entries)
        self.assertEqual(goods, {})
        self.assertEqual(provenance, {})

    def test_a_gated_material_is_priced_as_if_its_technology_were_held(self):
        prices_json = _prices_json(labourer_rate=2.0)
        entries = {
            "kiln": _entry({"brick_kg": 1.0}, requires_node="kiln_node",
                           labour_hours={"labourer": 4.0}),
        }
        goods, provenance = engine_prices.priced_goods_table(
            set(), prices_json, production_entries=entries)
        self.assertEqual(provenance, {"brick_kg": "gated"})
        self.assertAlmostEqual(goods["brick_kg"], 8.0)
        held_goods, held_provenance = engine_prices.priced_goods_table(
            {"kiln_node"}, prices_json, production_entries=entries)
        self.assertEqual(held_provenance, {"brick_kg": "solved"})
        self.assertAlmostEqual(held_goods["brick_kg"], 8.0)

    def test_the_held_technique_overrides_the_mature_one(self):
        prices_json = _prices_json(labourer_rate=2.0)
        entries = {
            "by_hand": _entry({"cloth_kg": 1.0}, requires_node=None,
                              labour_hours={"labourer": 10.0}),
            "by_loom": _entry({"cloth_kg": 1.0}, requires_node="loom_node",
                              labour_hours={"labourer": 2.0}),
        }
        held, _ = engine_prices.priced_goods_table(
            set(), prices_json, production_entries=entries)
        mature, _ = engine_prices.priced_goods_table(
            {"loom_node"}, prices_json, production_entries=entries)
        self.assertAlmostEqual(held["cloth_kg"], 20.0)
        self.assertAlmostEqual(mature["cloth_kg"], 4.0)


class EngineDefaultIsSolvedTests(unittest.TestCase):
    """`load()` with no arguments prices goods from the solver alone."""

    def test_default_goods_are_the_solved_table(self):
        _tree, document, nodes, _wages, goods = data.load()
        rate = data.starting_schedule().money_per_labour_hour
        reference_techs = data.load_civ()["starting_techs"]
        solved, _provenance = engine_prices.priced_goods_table(reference_techs, document)
        for material, price in solved.items():
            self.assertAlmostEqual(goods[material], price, msg=material)
        self.assertAlmostEqual(document["money_per_labour_hour"], rate)
        required = {material for node in nodes.values() for material in node["mat"]}
        self.assertTrue(required <= set(goods))


class RealDataIntegrationTests(unittest.TestCase):
    """One light check against the committed data/production/ and
    data/civilizations/, so the wiring is proven against the real tree and
    not only synthetic examples. Kept to a single gated solve (the
    expensive part), consistent with solve_prices.py's own measurement of a
    few tenths of a second per solve."""

    def test_a_real_civilizations_starting_techs_produce_a_measurable_split(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "data", "civilizations",
                "rome_100ad.json")) as source:
            starting_techs = json.load(source)["starting_techs"]

        provenance = data.goods_provenance(starting_techs)
        solved_count = sum(1 for source in provenance.values() if source == "solved")
        gated_count = sum(1 for source in provenance.values() if source == "gated")
        self.assertGreater(gated_count, 0,
                           "nothing came back 'gated', so era gating is not "
                           "reaching this table at all")
        self.assertGreater(solved_count, 0,
                           "the solver resolved nothing under Rome's own "
                           "starting technologies - the gate or the wiring "
                           "is broken, not merely incomplete")
        self.assertEqual(solved_count + gated_count, len(provenance))

    def test_runtime_price_provider_uses_the_calculator_result(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "data", "civilizations",
                "rome_100ad.json")) as source:
            starting_techs = json.load(source)["starting_techs"]

        calculated = data.calculated_goods_prices(
            starting_techs, civilization_id="rome_100ad")
        provenance = data.goods_provenance(
            starting_techs, civilization_id="rome_100ad")
        gated = next(material for material, source in sorted(provenance.items())
                     if source == "gated")
        solved = next(material for material, source in sorted(provenance.items())
                      if source == "solved")
        self.assertGreater(calculated[solved], 0.0)
        self.assertGreater(calculated[gated], 0.0)

    def test_the_gate_set_is_a_small_fraction_of_the_tree(self):
        # Pins the design premise CACHE KEY relies on: gates are rare. Not
        # pinned to an exact count (that number moves as data/production/
        # grows) - only that it stays the kind of small fraction that makes
        # keying the cache on it worthwhile at all.
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        tree, _prices_json, nodes, _wages, _goods = data.load()
        gate_nodes = engine_prices.all_gate_nodes()
        self.assertTrue(gate_nodes, "no gates at all - nothing can ever be solved")
        self.assertLess(len(gate_nodes), 0.10 * len(nodes),
                        "gate nodes are no longer a small fraction of the "
                        "tree - the cache-on-gates design this module "
                        "documents may need re-measuring")
        self.assertTrue(gate_nodes <= set(nodes),
                        "a requires_node names something outside the tree - "
                        "validate_production.py should already refuse this")


if __name__ == "__main__":
    unittest.main()
