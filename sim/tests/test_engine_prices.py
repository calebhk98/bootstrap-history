"""Checks `sim/engine/prices.py` - the first wiring of the price solver into
the engine, per the stakeholder's "prices.json should be slowly deleted."

Three things this pins, because getting any one of them wrong would defeat
the whole point of the module:

  - the cache is keyed on the set of GATE NODES HELD, not the full
    technology set - two technology sets that differ only outside the gate
    set must hit the same cache entry, and one that differs INSIDE it must
    miss;
  - the labour-hours -> denarii conversion is a multiplication by the
    labourer wage rate, the inverse of `solve_prices.py --compare`'s own
    division, not some other rate or direction;
  - the engine's default behaviour (`sim.engine.data.load()` with no
    arguments) is untouched - every existing call site calls it that way,
    and this module must not change what comes back until something opts
    in via `use_solved_prices`.

Written as unittest.TestCase against synthetic production entries, like
test_price_solver_cycles.py and test_price_solver_era_gate.py, so this does
not depend on the real, changing contents of data/production/ for anything
but one light integration check at the end.
"""
import json
import os
import sys
import unittest

from sim.engine import data, prices as engine_prices


def _prices_json(labourer_rate=2.0, smith_rate=4.0):
    """A minimal prices.json-shaped dict: just enough for
    wage_ratios_by_trade and denarii_per_labour_hour to read."""
    return {
        "wage_rates_denarii_per_hour": {
            "labourer": {"rate": labourer_rate},
            "smith": {"rate": smith_rate},
        },
        "purchase_prices_denarii": {},
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
    """LABOUR-HOURS TO DENARII: multiply by the labourer rate, matching
    `solve_prices.py --compare`'s own division inverted."""

    def test_one_labour_hour_is_worth_the_labourer_rate_in_denarii(self):
        prices_json = _prices_json(labourer_rate=3.5)
        self.assertEqual(
            engine_prices.hours_to_denarii(1.0, prices_json), 3.5)

    def test_round_trips_against_compares_own_division(self):
        # solve_prices.py --compare does book_hours = book_denarii / rate.
        # Converting back the other way must return the original figure -
        # anything else means the two tools disagree about the numeraire.
        prices_json = _prices_json(labourer_rate=2.5)
        rate = prices_json["wage_rates_denarii_per_hour"]["labourer"]["rate"]
        book_denarii = 40.0
        book_hours = book_denarii / rate
        self.assertAlmostEqual(
            engine_prices.hours_to_denarii(book_hours, prices_json), book_denarii)

    def test_the_smith_rate_is_not_used_for_the_labourer_conversion(self):
        # A wrong-rate bug (using whatever trade happened to be handy)
        # would rescale every solved price silently - the exact mistake the
        # module docstring calls out.
        prices_json = _prices_json(labourer_rate=2.0, smith_rate=9.0)
        self.assertEqual(engine_prices.denarii_per_labour_hour(prices_json), 2.0)


class PricedGoodsTableTests(unittest.TestCase):
    """`priced_goods_table` - the book overlay and its provenance report."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)

    def test_a_resolvable_material_is_marked_solved_and_converted(self):
        prices_json = _prices_json(labourer_rate=2.0)
        entries = {
            "straw": _entry({"straw_kg": 1.0}, requires_node=None,
                            labour_hours={"labourer": 3.0}),
        }
        book_goods = {"straw_kg": 999.0, "unrelated_kg": 5.0}
        goods, provenance = engine_prices.priced_goods_table(
            set(), book_goods, prices_json, production_entries=entries)

        self.assertEqual(provenance["straw_kg"], "solved")
        self.assertEqual(provenance["unrelated_kg"], "book")
        # 3 labour-hours at 2 denarii/hour = 6 denarii, replacing the book's
        # invented 999.
        self.assertAlmostEqual(goods["straw_kg"], 6.0)
        self.assertEqual(goods["unrelated_kg"], 5.0)

    def test_a_material_the_solver_cannot_reach_falls_back_to_the_book(self):
        prices_json = _prices_json()
        entries = {
            "requires_missing_input": _entry(
                {"widget_kg": 1.0}, inputs={"no_recipe_for_this_kg": 1.0},
                requires_node=None, labour_hours={"labourer": 1.0}),
        }
        book_goods = {"widget_kg": 42.0}
        goods, provenance = engine_prices.priced_goods_table(
            set(), book_goods, prices_json, production_entries=entries)
        self.assertEqual(provenance["widget_kg"], "book")
        self.assertEqual(goods["widget_kg"], 42.0)

    def test_the_solver_never_invents_a_material_the_book_never_had(self):
        prices_json = _prices_json()
        entries = {
            "straw": _entry({"straw_kg": 1.0}, requires_node=None,
                            labour_hours={"labourer": 1.0}),
        }
        goods, provenance = engine_prices.priced_goods_table(
            set(), {}, prices_json, production_entries=entries)
        self.assertEqual(goods, {})
        self.assertEqual(provenance, {})


class EngineDefaultBehaviourUnchangedTests(unittest.TestCase):
    """The commit's own hard requirement: `load()` with no arguments must
    behave exactly as it always has. `perf_fingerprint.py` is the real proof
    across whole playthroughs; this is the cheap, always-run version of the
    same claim."""

    def test_load_with_no_arguments_never_imports_the_solver(self):
        # sim.engine.prices is imported lazily, INSIDE the `if
        # use_solved_prices:` branch (see data.py's load()) specifically so
        # a default call cannot pay for, or risk, the solver at all. This
        # test's own module already imported it at the top of this file (to
        # reach `engine_prices` above), so the claim has to be checked by
        # removing it from sys.modules first and restoring whatever was
        # there afterwards - leaving the process's module cache exactly as
        # it found it, so later tests that DO opt in are not left importing
        # a second, uncached copy of the module.
        previously_imported = sys.modules.pop("sim.engine.prices", None)
        try:
            tree, prices_json, nodes, wages, goods = data.load()
            self.assertNotIn("sim.engine.prices", sys.modules)
        finally:
            if previously_imported is not None:
                sys.modules["sim.engine.prices"] = previously_imported
        self.assertTrue(goods)  # sanity: still loaded something real

    def test_goods_matches_the_book_exactly_by_default(self):
        tree, prices_json, nodes, wages, goods = data.load()
        book_goods = {key: value["p"]
                      for key, value in prices_json["purchase_prices_denarii"].items()
                      if not key.startswith("_")}
        self.assertEqual(goods, book_goods)


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
        book_count = sum(1 for source in provenance.values() if source == "book")

        self.assertGreater(solved_count, 0,
                           "the solver resolved nothing under Rome's own "
                           "starting technologies - the gate or the wiring "
                           "is broken, not merely incomplete")
        self.assertGreater(book_count, 0,
                           "every material resolved, which would mean this "
                           "test stopped exercising the fallback path")
        self.assertEqual(solved_count + book_count, len(provenance))

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
