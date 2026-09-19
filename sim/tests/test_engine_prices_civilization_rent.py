"""Checks the fix this round made to `sim/engine/prices.py`: `solved_prices`
now actually calls `solve_prices.rent_hours_per_kg_by_ore_material` and
`solve_prices.land_rent_hours_per_iugerum`, which it did not before - see
RENT WAS MISSING FROM THIS FILE in that module's own docstring, and
Complaints/43's own update sections for the finding this closes (the switch
would have made land free the moment it was flipped, even though
`sim/solve_prices.py`'s own CLI had already fixed that).

Three things pinned here, because getting any of them wrong silently
reintroduces the bug or introduces a new one of the same shape:

  - `solved_prices` (and `priced_goods_table`, and `sim.engine.data.load`/
    `goods_provenance` above it) actually price `iugerum_land` above zero
    once a civilization holds any territory - the CLI already proved this
    is possible; this file proves the ENGINE'S OWN wiring does it too, not
    only the standalone tool sitting next to it.
  - Land rent is genuinely PER CIVILIZATION - two civilizations holding the
    exact same gate-node set (easy to arrange with synthetic data, since
    gate nodes have nothing to do with territory) must not share a cached
    land price, because `sim/world/land.py` prices a civilization's own
    held regions, not its technology.
  - Leaving `civilization_id` unset behaves exactly as
    `solve_prices.DEFAULT_LAND_CIVILIZATION` (Rome) would, matching the
    CLI's own no-`--civ` default, so every EXISTING call site (which knows
    nothing of this new parameter) keeps behaving the way it always has.

Written against the real data/production/ and data/civilizations/, like
`test_engine_prices.py`'s own `RealDataIntegrationTests`, because the
thing being pinned - land actually differing by civilization - has no
useful synthetic analogue: land.py reads real geography.
"""
import json
import os
import unittest

from sim.engine import data, prices as engine_prices

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CIVDIR = os.path.join(ROOT, "data", "civilizations")


def _starting_techs(civilization_id):
    with open(os.path.join(CIVDIR, civilization_id + ".json")) as source:
        return json.load(source)["starting_techs"]


class RentIsWiredInTests(unittest.TestCase):
    """The headline fix: the engine's own switch no longer implies
    RENT_IS_ZERO the way it silently did before this round."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        with open(os.path.join(ROOT, "data", "prices.json")) as source:
            self.prices_json = json.load(source)

    def test_iugerum_land_is_no_longer_zero_for_rome(self):
        # UPDATE (stakeholder maintainability item 6, the two map
        # systems): this used to be 55.779 hours/iugerum, the number
        # Complaints/43's last update measured from the standalone CLI
        # (`python3 sim/solve_prices.py --civ rome_100ad`) back when
        # sim/world/land.py's extensive margin read Rome's SEVEN hand-drawn
        # `regions` records. It now reads `land_tiles` instead (see that
        # module's own docstring, UPDATE (stakeholder maintainability item
        # 6...) section) - 88 tiles instead of 7 regions for Rome - and
        # the number moved for two measured, physically sensible reasons,
        # not because anything here broke:
        #   1. north_africa's own single blended fertility_quality_
        #      multiplier (1.35 - Complaints/46's own "96% Sahara, rated on
        #      the strength of the Nile") does not survive contact with
        #      its own 47 real tiles: they range 0.546-0.935 (measured
        #      directly off data/world/geography.json's land_tiles), so
        #      even the BEST of them is below the old blended 1.35 - the
        #      extensive margin's own ceiling fertility fell.
        #   2. Rome's own total arable endowment, summed over real tiles
        #      rather than one book arable_fraction per region, came out
        #      about 13% LARGER (measured directly against sim/world/
        #      land.py's own cultivable_land_for_civilization, region-grain
        #      vs tile-grain), which thins the intensive margin's own
        #      labour-per-iugerum figure and so its own rent contribution.
        # Both effects push the price DOWN, which is what happened: this
        # task's own report has the full before/after account, including
        # the same measurement for Han China. This is exactly the kind of
        # deliberate baseline shift CLAUDE.md SS3.2 describes ("every step
        # toward endogeneity costs historical match in the short run") -
        # the number the test pins is UPDATED to match the new, more
        # physically grounded mechanism, not reverted to the old one.
        result = engine_prices.solved_prices(
            _starting_techs("rome_100ad"), self.prices_json,
            civilization_id="rome_100ad")
        self.assertIn("iugerum_land", result.prices_in_labour_hours)
        self.assertAlmostEqual(
            result.prices_in_labour_hours["iugerum_land"], 35.986, places=2)

    def test_omitting_civilization_id_defaults_to_rome(self):
        with_default = engine_prices.solved_prices(
            _starting_techs("rome_100ad"), self.prices_json)
        with_explicit_rome = engine_prices.solved_prices(
            _starting_techs("rome_100ad"), self.prices_json,
            civilization_id="rome_100ad")
        self.assertIs(with_default, with_explicit_rome,
                      "omitting civilization_id must hit the same cache "
                      "entry as explicitly naming solve_prices."
                      "DEFAULT_LAND_CIVILIZATION")


class LandRentIsPerCivilizationTests(unittest.TestCase):
    """Two civilizations must not share a land price just because they
    happen to hold the same gate nodes - see RENT NEEDS A CIVILIZATION in
    sim/engine/prices.py's module docstring."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        with open(os.path.join(ROOT, "data", "prices.json")) as source:
            self.prices_json = json.load(source)

    def test_rome_and_han_china_get_different_land_rents(self):
        # Real starting_techs for two real civilizations - if their gate
        # intersections happened to coincide, a cache keyed on gate nodes
        # ALONE would silently hand one of them the other's land price.
        rome = engine_prices.solved_prices(
            _starting_techs("rome_100ad"), self.prices_json,
            civilization_id="rome_100ad")
        han = engine_prices.solved_prices(
            _starting_techs("han_china_100ad"), self.prices_json,
            civilization_id="han_china_100ad")
        self.assertIn("iugerum_land", rome.prices_in_labour_hours)
        self.assertIn("iugerum_land", han.prices_in_labour_hours)
        self.assertNotAlmostEqual(
            rome.prices_in_labour_hours["iugerum_land"],
            han.prices_in_labour_hours["iugerum_land"], places=2)

    def test_same_gate_nodes_different_civilization_id_is_a_cache_miss(self):
        # Fabricate the hazard directly rather than hoping two real
        # civilizations' gate intersections happen to collide: same held
        # technology set, same production_entries object, different
        # civilization_id only. If the cache key were gate-nodes-only,
        # these would incorrectly share one cached SolvedPrices.
        held = set(_starting_techs("rome_100ad"))
        rome = engine_prices.solved_prices(
            held, self.prices_json, civilization_id="rome_100ad")
        han = engine_prices.solved_prices(
            held, self.prices_json, civilization_id="han_china_100ad")
        self.assertIsNot(rome, han)
        self.assertNotAlmostEqual(
            rome.prices_in_labour_hours["iugerum_land"],
            han.prices_in_labour_hours["iugerum_land"], places=2)

    def test_result_records_which_civilization_it_was_solved_for(self):
        result = engine_prices.solved_prices(
            _starting_techs("mexica_1500"), self.prices_json,
            civilization_id="mexica_1500")
        self.assertEqual(result.civilization_id, "mexica_1500")


class GoodsProvenanceCivilizationTests(unittest.TestCase):
    """`sim.engine.data.goods_provenance` and `load` thread civilization_id
    through to the same place - the caller-facing surface of the fix."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)

    def test_goods_provenance_prices_iugerum_land_as_solved(self):
        provenance = data.goods_provenance(
            _starting_techs("rome_100ad"), civilization_id="rome_100ad")
        self.assertEqual(provenance.get("iugerum_land"), "solved")

    def test_load_with_use_solved_prices_produces_a_nonzero_land_price(self):
        _tree, prices_json, _nodes, _wages, goods = data.load(
            use_solved_prices=True,
            held_technology_ids=_starting_techs("rome_100ad"),
            civilization_id="rome_100ad")
        self.assertIn("iugerum_land", goods)
        self.assertGreater(goods["iugerum_land"], 0.0)


if __name__ == "__main__":
    unittest.main()
