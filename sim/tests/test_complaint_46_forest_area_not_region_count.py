"""Regression coverage for Complaints/46, the forest half of it.

Complaints/46 names land RENT as the place a region-count-as-area proxy
leaks into the economics (a region is a filing label, not a unit of area,
and the labels range 86x in size - data/world/geography.json). The
stakeholder's own follow-up observation pointed at a SECOND place the same
failure was hiding: `Sim.forest_land_ceiling()` in sim/engine/economy.py
used to scale standing woodland by `len(home_regions)`, the COUNT of labels
a civilization's territory happens to be filed under, not by how much
ground any of those labels actually cover. Re-filing the same territory
under a different number of labels used to change how much forest you could
hold, with not one hectare of ground changing hands.

Not registered in sim/tests/__main__.py's TOPICS list yet - the agent that
wrote this file owns only sim/engine/economy.py and test files (see its own
task's constraints). Needs "complaint_46_forest_area_not_region_count"
added there for `test_regressions.py` to run it as part of the full suite.
"""
from .harness import *  # noqa: F401,F403


def _fresh_sim():
    """A rome_100ad Sim, used only as a vehicle for calling the geography/
    forest methods under test - its own home_regions and state_capacity are
    overwritten per-check below via s.civ, exactly the same dict
    forest_land_ceiling() itself reads with self.civ.get(...)."""
    return sim(civ="rome_100ad")


# --- 1. home_land_area_km2() reads geography.json's own land.land_area_km2
# per home region, summed - not a count of how many regions there are.
_s = _fresh_sim()
_s.civ = dict(_s.civ)
_s.civ["home_regions"] = ["italia"]
_italia_area = _s.home_land_area_km2()
check("home_land_area_km2() of a single region equals that region's own "
      "geography.json land.land_area_km2, not '1 region'",
      _italia_area == _s._regions["italia"]["land"]["land_area_km2"],
      _italia_area)

_s.civ["home_regions"] = ["italia", "britannia"]
_two_region_area = _s.home_land_area_km2()
check("home_land_area_km2() of two home regions is the SUM of their real "
      "areas, not a count of 2",
      _two_region_area == (_s._regions["italia"]["land"]["land_area_km2"]
                            + _s._regions["britannia"]["land"]["land_area_km2"]),
      _two_region_area)


# --- 2. THE REAL TEST: two territories of nearly identical AREA but wildly
# different REGION COUNT must get nearly identical forest ceilings, and two
# territories of nearly identical region COUNT but wildly different AREA
# must not. This is exactly the china-vs-rome shape Complaints/46 measures
# for rent, applied here to forest.
_rome = _fresh_sim()
_han = _fresh_sim()
_han.civ = dict(_han.civ)
_han.civ["home_regions"] = ["china"]          # 1 region, 9,597,000 km2
_han.civ["state_capacity"] = _rome.civ["state_capacity"]   # isolate area, not state capacity

_rome_area = _rome.home_land_area_km2()
_han_area = _han.home_land_area_km2()
_rome_ceiling = _rome.forest_land_ceiling()
_han_ceiling = _han.forest_land_ceiling()

check("Rome (7 regions) and a synthetic single-region China stand-in have "
      "land areas within 1% of each other, per Complaints/46's own measurement",
      abs(_rome_area - _han_area) / max(_rome_area, _han_area) < 0.01,
      (_rome_area, _han_area))
check("...and with state_capacity held equal, their forest ceilings land "
      "within 10% of each other too - AREA, not region count, is what should "
      "decide this",
      abs(_rome_ceiling - _han_ceiling) / max(_rome_ceiling, _han_ceiling) < 0.10,
      (_rome_ceiling, _han_ceiling))

# --- 3. Doubling the region COUNT while holding AREA fixed must not move
# the ceiling at all: relabelling the same ground under a different number
# of filing categories is not a different amount of ground. Splitting one
# region into two labels of the same combined area is not directly
# expressible without editing data/, so instead this compares two DIFFERENT
# home_regions sets that happen to sum to nearly the same total real area:
# a single region (gaul_germania, 981,000 km2) against two others summing to
# within 1% of it (britannia + levant_mesopotamia, 974,000 km2).
_a = _fresh_sim()
_a.civ = dict(_a.civ)
_a.civ["home_regions"] = ["gaul_germania"]                    # 1 region, 981,000 km2
_b = _fresh_sim()
_b.civ = dict(_b.civ)
_b.civ["home_regions"] = ["britannia", "levant_mesopotamia"]  # 2 regions, 974,000 km2
_a_area = _a.home_land_area_km2()
_b_area = _b.home_land_area_km2()
# These are real geography.json figures, not tuned to match; only proceed
# with the strict comparison if they are in fact close, and report the gap
# either way so a future geography.json edit that breaks this assumption is
# visible rather than silently skipped.
if abs(_a_area - _b_area) / max(_a_area, _b_area) < 0.05:
    _a.civ["state_capacity"] = _b.civ["state_capacity"]
    check("a 1-region territory and a 2-region territory of nearly the same "
          "real area get nearly the same forest ceiling",
          abs(_a.forest_land_ceiling() - _b.forest_land_ceiling())
          / max(_a.forest_land_ceiling(), _b.forest_land_ceiling()) < 0.05,
          (_a_area, _b_area, _a.forest_land_ceiling(), _b.forest_land_ceiling()))
else:
    check("gaul_germania and britannia+levant_mesopotamia are close enough "
          "in area for the count-invariance check above to be meaningful",
          False, (_a_area, _b_area))


# --- 4. Rome's own ceiling should move only a little from the pre-fix
# region-count formula, because Rome's SEVEN regions happen to be close to
# what the region-count formula was tuned against - the fix is a
# recalibration of what varies, not a deliberate change to Rome's own
# number. (31,325 ha is the old formula's exact pre-revenue result for
# rome_100ad's real home_regions/state_capacity, computed by hand from the
# constants this file replaced.)
_rome_plain = _fresh_sim()
_rome_pre_revenue_new = (
    (_rome_plain.FOREST_HA_PER_MILLION_KM2_BASE
     + _rome_plain.FOREST_HA_PER_MILLION_KM2_PER_SC
       * float(_rome_plain.civ.get("state_capacity", _rome_plain.STATE_CAPACITY_DEFAULT_FALLBACK)))
    * (_rome_plain.home_land_area_km2() / 1.0e6))
_OLD_ROME_PRE_REVENUE = 31325.0
check("Rome's own pre-revenue forest ceiling under the area-based formula "
      "is within 5% of the old region-count formula's figure for Rome "
      "specifically - the fix should barely move the one territory its old "
      "constants were tuned against",
      abs(_rome_pre_revenue_new - _OLD_ROME_PRE_REVENUE) / _OLD_ROME_PRE_REVENUE < 0.05,
      _rome_pre_revenue_new)


# --- 5. A civilization with no valid home_regions at all must not crash -
# home_land_area_km2() falls back the same way _compute_home_centroid()
# already does, rather than raising or returning zero.
_orphan = _fresh_sim()
_orphan.civ = dict(_orphan.civ)
_orphan.civ["home_regions"] = ["not_a_real_region_id"]
_orphan_area = _orphan.home_land_area_km2()
check("a civ file with no valid home_regions gets a positive fallback area, "
      "not a crash or a silent zero that would make forest_land_ceiling() "
      "always refuse every purchase",
      _orphan_area > 0.0,
      _orphan_area)
check("...and forest_land_ceiling() itself still returns a usable positive "
      "number in that situation",
      _orphan.forest_land_ceiling() > 0.0,
      _orphan.forest_land_ceiling())
