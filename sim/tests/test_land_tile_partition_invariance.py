"""THE RE-PARTITIONING INVARIANCE TEST (stakeholder maintainability item 6).

Complaints/46 (`forest_land_ceiling` scaled by `len(home_regions)`, so Han
China at 9,597,000 km2 filed as ONE region reached a seventh of Rome's
firewood on the SAME ground filed as SEVEN) and Complaints/50 (a region
record was one weather draw, so China flipped one coin where Rome flipped
seven) are the same defect, stated twice: a hand-drawn `regions` record was
used as if it were a unit of PHYSICAL QUANTITY, when it is only a LABEL -
how many boxes a mapmaker happened to draw. `sim/world/land.py`'s own
extensive margin (`cultivable_land_for_civilization`, `find_margin_of_
cultivation`) is the third mechanism this pattern touches, and this file
is the test that would have caught all three, run against the one that
was never fixed before this change.

THE PROPERTY, STATED PRECISELY. Take a civilization's territory - some
set of physical land. Describe that SAME territory two different ways: as
ONE region record, or as several region records that between them cover
EXACTLY the same ground (same total area, same total arable land, the
same underlying quality distributed the same way - an "identically-
summing" split, never a different or invented parcel). Every land figure
`sim/world/land.py` computes for that territory - the parcels it returns,
the marginal parcel, the price, the quantity supplied, the unmet demand,
the labour intensity - must be EXACTLY the same regardless of which of
the two descriptions is on file. Nothing here should be sensitive to how
many labels a civilization's `home_regions` happens to name, or what
those labels are called - only to the physical land itself.

WHY THIS MODULE (NOT sim/tests/) OWNS THIS TEST. Per this task's own
working agreement, `sim/tests/` is owned by other agents concurrently
editing this checkout; `sim/world/land.py` and any new `sim/world/land_*`
file are this task's own territory. This file's name starts with `land_`
for exactly that reason. It is NOT wired into `sim/tests/__main__.py`'s
own `TOPICS` list (that file is under `sim/tests/` too) - see this task's
own final report for the one-line addition that would register it there
(`"land_tile_partition_invariance"` alongside `"land"`) if whoever owns
that file wants to take it. Runnable directly:

    python3 -m unittest sim.world.land_tile_partition_invariance_test -v

or as a plain script:

    python3 sim/world/land_tile_partition_invariance_test.py

THE FIXTURE. Four synthetic tiles (never real geography.json data, so
this test's own numbers do not drift when that file's real tiles are
regenerated at a finer grid - see `docs/architecture/MAP_AND_WEATHER.md`
section 5, stage 4), t1..t4, all the same land_area_km2 and
arable_fraction so every "split" below is trivially area-and-arable-
identical, differing only in fertility_quality_multiplier (1.5, 1.2, 0.8,
0.5 - a real spread, not four copies of the same number, because a test
that cannot tell "best" from "worst" cannot prove the margin survived a
re-partition). The SAME four tiles are described under THREE different
region groupings, each identically summing to the same physical total:

    "whole"          -> [t1, t2, t3, t4]   (one label)
    "north"/"south"  -> [t1, t2] / [t3, t4]   (two labels)
    "r_t1".."r_t4"   -> one tile each         (four labels, one per tile)

The fixture geography dict carries BOTH a `land_tiles` block (what the
POST-migration `cultivable_land_for_civilization` reads) AND honestly-
aggregated `regions` blocks for "whole"/"north"/"south" (what the PRE-
migration mechanism read) - the region-level fertility for "north" is the
true area-weighted average of t1 and t2 (1.35), "south" of t3 and t4
(0.65), and "whole" of all four (1.0); 1.35 and 0.65 average back to
exactly 1.0 at equal weight, so this really is an identically-summing
split by the pre-migration mechanism's own arithmetic, not a different
scenario dressed up as the same one. This lets the SAME test file exercise
BOTH mechanisms: run against this checkout's `sim.world.land` (tile-
grain, post-migration) every assertion below passes; run against a
checkout from before this change (region-grain, `regions` only - the
`land_tiles` block is simply extra data that mechanism never reads) the
SAME assertions fail, because that mechanism's own atomic unit was a
region record, so "whole" (one blended fertility, zero internal margin)
and "north"+"south" (two distinct fertilities, a real internal margin
between them) are NOT the same answer to it, even though they describe
the same ground.
"""
import unittest

from sim.world import land

_TILE_LAND_AREA_KM2 = 100_000.0
_TILE_ARABLE_FRACTION = 0.5

_TILE_FERTILITY = {
    "t1": 1.5,
    "t2": 1.2,
    "t3": 0.8,
    "t4": 0.5,
}


def _tile_block(fertility):
    return {
        "land_area_km2": _TILE_LAND_AREA_KM2,
        "arable_fraction": _TILE_ARABLE_FRACTION,
        "fertility_quality_multiplier": fertility,
        "conf": "D",
        "source": "sim/world/land_tile_partition_invariance_test.py "
                  "synthetic fixture - never real geography.json data.",
    }


def _region_block(tile_ids):
    # The HONEST region-level aggregate a pre-migration author would have
    # written by hand for a region covering exactly these tiles: same
    # discipline this module's own `_declare_land_area`/`_declare_arable_
    # fraction`/`_declare_fertility` document - area sums, arable_fraction
    # is unchanged because every tile here shares the same one, and
    # fertility is the true area-weighted average (equal weights, because
    # every tile here has the same area and arable_fraction).
    n = len(tile_ids)
    area = _TILE_LAND_AREA_KM2 * n
    fertility = sum(_TILE_FERTILITY[t] for t in tile_ids) / n
    return {
        "land": {
            "land_area_km2": area,
            "arable_fraction": _TILE_ARABLE_FRACTION,
            "fertility_quality_multiplier": fertility,
            "conf": "D",
            "source": "sim/world/land_tile_partition_invariance_test.py "
                      "synthetic fixture - area-weighted average over %s, "
                      "an HONEST aggregate, not a different scenario."
                      % ", ".join(tile_ids),
        }
    }


_GEOGRAPHY = {
    "regions": {
        "whole": _region_block(["t1", "t2", "t3", "t4"]),
        "north": _region_block(["t1", "t2"]),
        "south": _region_block(["t3", "t4"]),
        "r_t1": _region_block(["t1"]),
        "r_t2": _region_block(["t2"]),
        "r_t3": _region_block(["t3"]),
        "r_t4": _region_block(["t4"]),
    },
    "land_tiles": {
        "tiles": {
            tile_id: _tile_block(fertility)
            for tile_id, fertility in _TILE_FERTILITY.items()
        },
        "region_to_tiles": {
            "whole": ["t1", "t2", "t3", "t4"],
            "north": ["t1", "t2"],
            "south": ["t3", "t4"],
            "r_t1": ["t1"],
            "r_t2": ["t2"],
            "r_t3": ["t3"],
            "r_t4": ["t4"],
        },
        "unmapped_tile_count": 0,
    },
}

_POPULATION = 100.0

_CIVILIZATIONS = {
    "one_label": {"home_regions": ["whole"], "population": _POPULATION},
    "two_labels": {"home_regions": ["north", "south"], "population": _POPULATION},
    "four_labels": {"home_regions": ["r_t1", "r_t2", "r_t3", "r_t4"],
                    "population": _POPULATION},
}


def _land_set(civilization_id):
    """The territory `cultivable_land_for_civilization` returns, as a
    frozenset of plain tuples rather than RegionLand namedtuples directly
    - RegionLand's own `region` field is a TILE id post-migration and a
    REGION key pre-migration, so comparing the tuple's `region` entry
    across the three civilizations below is exactly the "does this depend
    on the label" question this test asks; everything else in the tuple
    is a physical quantity that should match regardless.
    """
    parcels = land.cultivable_land_for_civilization(
        civilization_id, geography=_GEOGRAPHY, civilizations=_CIVILIZATIONS)
    return frozenset(
        (parcel.land_area_km2, parcel.arable_fraction,
         parcel.fertility_quality_multiplier, round(parcel.arable_iugera, 6))
        for parcel in parcels)


class TilePartitionInvarianceTests(unittest.TestCase):
    """Post-migration (`sim.world.land` reading `land_tiles`): PASSES.
    Pre-migration (`sim.world.land` reading `regions` alone): FAILS - see
    this module's own docstring for why, and this task's report for the
    confirmation run against the pre-change checkout.
    """

    def test_territory_is_the_same_physical_quantities_regardless_of_label_count(self):
        # The SET of (area, arable_fraction, fertility, arable_iugera)
        # tuples held must be identical whether the four tiles are filed
        # as one region, two, or four - this is the property Complaints/
        # 46 and 50 were each separately about, made explicit and testable
        # for land.py's own mechanism.
        one = _land_set("one_label")
        two = _land_set("two_labels")
        four = _land_set("four_labels")
        self.assertEqual(one, two)
        self.assertEqual(one, four)
        # Not a vacuous comparison of three empty sets, and not a
        # comparison that happens to pass because every tile has the same
        # fertility - four DISTINCT fertilities are actually present.
        self.assertEqual(len(one), 4)
        self.assertEqual(
            {row[2] for row in one}, {1.5, 1.2, 0.8, 0.5})

    def test_margin_outcome_is_unchanged_by_relabeling(self):
        one = land.margin_outcome_for_civilization(
            "one_label", geography=_GEOGRAPHY, civilizations=_CIVILIZATIONS)
        two = land.margin_outcome_for_civilization(
            "two_labels", geography=_GEOGRAPHY, civilizations=_CIVILIZATIONS)
        four = land.margin_outcome_for_civilization(
            "four_labels", geography=_GEOGRAPHY, civilizations=_CIVILIZATIONS)
        for other in (two, four):
            self.assertAlmostEqual(
                one.quantity_demanded_kg, other.quantity_demanded_kg)
            self.assertAlmostEqual(
                one.quantity_supplied_kg, other.quantity_supplied_kg)
            self.assertAlmostEqual(
                one.unmet_demand_kg, other.unmet_demand_kg)
            self.assertAlmostEqual(
                one.price_kg_grain_equivalent_per_iugerum,
                other.price_kg_grain_equivalent_per_iugerum)
            self.assertAlmostEqual(
                one.labour_hours_per_iugerum, other.labour_hours_per_iugerum)
            # The MARGINAL PARCEL is the same physical tile too, not merely
            # the same fertility - post-migration, `marginal_region` is a
            # tile id, and a tile's own id does not change no matter which
            # region label currently claims it.
            self.assertEqual(one.marginal_region, other.marginal_region)

    def test_price_is_strictly_positive_so_this_is_not_a_zero_everywhere_fixture(self):
        # If every quantity above happened to be 0.0 regardless of
        # relabeling, the test would pass for the uninteresting reason
        # that there is nothing to distinguish - guard against that.
        one = land.margin_outcome_for_civilization(
            "one_label", geography=_GEOGRAPHY, civilizations=_CIVILIZATIONS)
        self.assertGreater(one.price_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertGreater(one.quantity_supplied_kg, 0.0)


if __name__ == "__main__":
    unittest.main()
