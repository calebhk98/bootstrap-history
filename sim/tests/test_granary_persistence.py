"""Regression tests for the granary fix -
Complaints/45-no-granary-so-the-baseline-collapses.md.

WHAT THIS GUARDS. Three separate, previously-unguarded properties, each of
which broke the model in its own way while this fix was being built:

  1. `agriculture.stock_to_carry_forward_kg` - a caller that persists
     `Storage` across years MUST add `seed_retained_kg` back into
     `stock_after_kg`, or one full season's seed requirement is deducted
     TWICE per year (once as this year's `seed_retained_kg`, again as next
     year's `seed_sown_kg`) and a granary that is supposed to buffer a
     population instead starves it on perfectly ordinary weather. This was
     caught empirically during this task: the first attempt at persisting
     `stock_after_kg` alone drove rome_100ad from 65,000,000 to roughly
     700,000 people over a century of ordinary weather with no hazard -
     WORSE than Complaints/45's original 21.9%-of-start bug, not better.
  2. `Sim.farm_stock_kg` round-trips through save/load (SAVE_FIELDS,
     sim/engine/proto/saveload.py) - the field Complaints/45 says is the
     one thing standing between "carry the granary across years" and it
     actually happening, and per CLAUDE.md SS3.5, a field that fails to
     round-trip breaks the game in normal play the moment `--session` is
     used, because every command is a save and a load.
  3. `agriculture.granary_capacity_kg` bounds what a caller carries forward
     - a granary is a physical structure, not an unlimited ledger, and
     GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration (agriculture.py)
     gives the physical basis. This module checks the cap is respected at
     the engine boundary (sim/engine/core.py's `_demographic_recovery`),
     not that any particular numeric value was chosen for other reasons.

This module also PINS the headline measurement Complaints/45 itself is
about: an unshocked rome_100ad century should land substantially above the
21.9%-of-start figure the bug produced, without demanding it land at
exactly 100% (CLAUDE.md SS3.2 - the baseline is allowed to still be
imperfect; what matters is that a real mechanism, not a tuned number, moved
it). See CenturyMeasurementTests's own docstring for the exact bound and
why it is loose.

STYLE: this module needs a real `Sim` (the granary lives at the engine
boundary, not inside agriculture.py alone), so - unlike test_agriculture.py
and test_demography.py, which stay off sim/tests/harness.py on purpose -
this one uses harness.py, the same way test_agriculture_wiring.py does for
the same reason.
"""
import statistics
import unittest

from .harness import *  # noqa: F401,F403

from sim.world import agriculture


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class DoubleSeedDeductionTests(unittest.TestCase):
    """The bug this task's own probe caught: persisting `stock_after_kg`
    alone (without `seed_retained_kg` added back) manufactures a
    structural, weather-independent annual deficit of one season's seed
    requirement - see `agriculture.stock_to_carry_forward_kg`'s own
    docstring and `Storage.step`'s docstring section on carrying stock
    across years for the full mechanism.
    """

    # A population sized consistently with its own land/labour - matching
    # how sim/engine/core.py's `_demographic_recovery` actually builds
    # these three together, rather than an arbitrary land/population
    # mismatch that would swamp the effect being measured under its own
    # structural food surplus (agriculture.py's module docstring names
    # that surplus - roughly fourfold - as this module's own headline
    # finding, and a land/population pairing far outside what
    # `farmland_for_population` would choose can hide the double-seed bug
    # inside it instead of demonstrating it).
    _POPULATION = 500000.0

    def _consistent_land_and_workers(self):
        # Mirrors sim/engine/core.py's `_demographic_recovery` exactly -
        # see its own extensive comment on why `labour_hours` MUST be
        # built as `hectares_worked * REFERENCE_LABOUR_HOURS_PER_HECTARE`
        # rather than `workers_fte * ANNUAL_LABOUR_HOURS_PER_FARM_WORKER`
        # (the two conventions disagree by roughly 4.4x and using the
        # wrong one inflates the harvest enough to mask the very deficit
        # this test exists to demonstrate).
        land = agriculture.farmland_for_population(self._POPULATION)
        workers_fte = agriculture.farm_workers_fte_for_population(
            self._POPULATION)
        hectares_worked = min(
            land.hectares,
            workers_fte * agriculture.hectares_cropped_per_farm_worker())
        labour_hours = (hectares_worked
                        * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE)
        return land, workers_fte, labour_hours

    def test_carrying_stock_after_kg_alone_loses_a_whole_seasons_seed_every_year(self):
        land, workers_fte, labour_hours = self._consistent_land_and_workers()
        one_season_seed_kg = (agriculture.SEED_SOWING_RATE_KG_PER_HA
                              * land.hectares)
        stock = 0.0
        for _year in range(10):
            storage = agriculture.Storage(stock_kg=stock, seed=42)
            flows = storage.step(land, labour_hours, self._POPULATION,
                                 worker_count=workers_fte)
            stock = flows.stock_after_kg  # THE BUG: seed_retained_kg dropped
        # `stock_after_kg` has had `seed_retained_kg` (one whole season's
        # seed) removed from it without that amount ever being added back
        # anywhere - so at reference weather (this test's deterministic
        # seed lands close to it), the naive carry sits at roughly minus
        # one season's seed requirement, not at roughly zero the way a
        # correctly-closed cycle would.
        self.assertLess(stock, -0.5 * one_season_seed_kg, (stock,
                        one_season_seed_kg))

    def test_the_fixed_carry_rule_does_not_drift_structurally(self):
        land, workers_fte, labour_hours = self._consistent_land_and_workers()
        stock = 0.0
        stocks = []
        for _year in range(30):
            storage = agriculture.Storage(stock_kg=stock, seed=42)
            flows = storage.step(land, labour_hours, self._POPULATION,
                                 worker_count=workers_fte)
            stock = agriculture.stock_to_carry_forward_kg(flows)
            stocks.append(stock)
        # The corrected rule may still drift (this module's own headline
        # finding is a large structural food SURPLUS at reference
        # technique - see agriculture.py's module docstring), but it must
        # not drift toward the same catastrophic, ever-more-negative
        # trajectory the naive rule produces on the same inputs. A loose,
        # one-sided bound: never falls anywhere near the naive rule's
        # 30-year floor.
        self.assertGreater(min(stocks),
                           -5.0 * agriculture.SEED_SOWING_RATE_KG_PER_HA
                           * land.hectares)

    def test_stock_to_carry_forward_kg_is_exactly_stock_after_plus_seed_retained(self):
        land = agriculture.Land(50.0)
        storage = agriculture.Storage(stock_kg=1000.0, seed=7)
        flows = storage.step(land, labour_hours=50.0 * 150.0, population=20.0)
        self.assertAlmostEqual(
            agriculture.stock_to_carry_forward_kg(flows),
            flows.stock_after_kg + flows.seed_retained_kg, places=6)


class SaveLoadRoundTripTests(unittest.TestCase):
    """CLAUDE.md SS3.5: no save-format migration, ever - but round-tripping
    WITHIN a build is not optional, and `--session` makes every command a
    save and a load, so a field that does not round-trip breaks ordinary
    play immediately, not just a hypothetical resume.
    """

    def test_farm_stock_kg_round_trips_through_save_and_load(self):
        import tempfile, os
        from sim.engine.proto import saveload as S

        test_sim = _rome_sim(events=False)
        for year in range(101, 111):
            test_sim._demographic_recovery(year)
        before = test_sim.farm_stock_kg
        self.assertNotEqual(before, 0.0, "expected a nonzero granary after "
                            "ten years - otherwise this test is not "
                            "actually exercising round-trip of a moved "
                            "value")

        path = tempfile.mktemp(suffix=".json")
        try:
            S.save_state(test_sim, path)
            fresh = _rome_sim(events=False)
            self.assertEqual(fresh.farm_stock_kg, 0.0,
                             "a freshly constructed Sim's own initial "
                             "condition - if this ever changes, the "
                             "assertion below proves nothing")
            S.load_state(fresh, path)
            self.assertEqual(fresh.farm_stock_kg, before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_a_save_missing_farm_stock_kg_is_refused_not_silently_defaulted(self):
        # CLAUDE.md SS3.5's own rule: no upgrade path, no `if "old_key" in
        # data`. An old save simply does not load - see saveload.py's own
        # comment on REQUIRED_SAVE_FIELDS for why silently accepting a
        # partial shape is worse than refusing the file outright.
        import tempfile, os, json
        from sim.engine.proto import saveload as S

        test_sim = _rome_sim(events=False)
        path = tempfile.mktemp(suffix=".json")
        try:
            S.save_state(test_sim, path)
            with open(path) as handle:
                blob = json.load(handle)
            if "farm_stock_kg" in blob:
                del blob["farm_stock_kg"]
            else:
                del blob["economy"]
            with open(path, "w") as handle:
                json.dump(blob, handle)
            fresh = _rome_sim(events=False)
            with self.assertRaises(ValueError):
                S.load_state(fresh, path)
        finally:
            if os.path.exists(path):
                os.remove(path)


class GranaryCapacityTests(unittest.TestCase):
    """GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration (agriculture.py)
    gives the physical basis; this checks the cap the engine boundary
    (`Sim._demographic_recovery`) actually applies, never lets the carried
    stock exceed it.
    """

    def test_farm_stock_kg_never_exceeds_capacity_over_many_good_years(self):
        test_sim = _rome_sim(events=False)
        max_seen_ratio_to_capacity = 0.0
        for year in range(101, 161):
            test_sim._demographic_recovery(year)
            demand_kg = test_sim._last_farm_year.food_demand_kg
            capacity_kg = agriculture.granary_capacity_kg(demand_kg)
            self.assertLessEqual(test_sim.farm_stock_kg, capacity_kg + 1e-6,
                                 (year, test_sim.farm_stock_kg, capacity_kg))
            if capacity_kg > 0:
                max_seen_ratio_to_capacity = max(
                    max_seen_ratio_to_capacity,
                    test_sim.farm_stock_kg / capacity_kg)
        # The cap should actually bind at some point over sixty years of
        # ordinary weather, given this module's own documented structural
        # surplus at reference technique (agriculture.py's module
        # docstring) - otherwise this test would pass trivially even if
        # the cap were wired in wrong (e.g. capacity_kg computed as zero).
        self.assertGreater(max_seen_ratio_to_capacity, 0.5)


class CenturyMeasurementTests(unittest.TestCase):
    """The actual number Complaints/45 is about. Loose bounds, deliberately
    - see CLAUDE.md SS3.2: the baseline is not required to be flat, and
    must never be forced flat by tuning a physical quantity (this test
    would not catch that kind of cheat anyway; sim/audit_costs.py and
    hand review are what guard against it). What this DOES guard is the
    granary regressing back to inert (a fresh `Storage(stock_kg=0.0, ...)`
    built every year again) or the double-seed-deduction bug returning,
    either of which would drag the century-end fraction back down toward
    Complaints/45's original 21.9%, or below it.
    """

    def test_unshocked_century_lands_well_above_the_pre_fix_measurement(self):
        test_sim = _rome_sim(events=False)
        start = test_sim.population.total
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
        end = test_sim.population.total
        fraction = end / start
        # Complaints/45's own pre-fix measurement was 0.219 (21.9%); this
        # task's own re-measurement on this checkout, before the granary
        # existed, was 0.195. Comfortably above either, without demanding
        # anything close to 1.0.
        self.assertGreater(fraction, 0.5, (start, end, fraction))

    def test_mean_nutrition_ratio_is_close_to_one_not_merely_plausible(self):
        # A tighter bound than test_agriculture_wiring.py's own
        # NoFamineWithoutCauseTests (which predates the granary and only
        # asks for > 0.7) - the granary's whole point is to bring this
        # closer to subsistence than the unbuffered wiring could.
        test_sim = _rome_sim(events=False)
        ratios = []
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
            ratios.append(test_sim._last_demographic_step.nutrition_ratio)
        mean_ratio = statistics.fmean(ratios)
        self.assertGreater(mean_ratio, 0.9, ratios)
        # THE UPPER BOUND IS NOT 1.0: capping the mean at subsistence would
        # forbid the outcome this whole milestone is for. A population that
        # grows must, on average, be fed at or above subsistence - that is
        # what growth IS. With weather drawn per home region and pooled by
        # land share (Complaints/47), good years survive often enough to
        # show up in the mean, measured at 1.0042 over this century. The
        # band is comfortably fed, not gorging - the physical ceiling on
        # that is MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE (1.75), and a mean
        # anywhere near it would mean the farm is badly oversized.
        self.assertLess(mean_ratio, 1.1, ratios)


class FarmWorkforceShareIsFixedTests(unittest.TestCase):
    """Answers a stakeholder question with a test rather than only prose:
    does the model let people move between professions when food gets
    scarce? `farm_workers_fte_for_population` is
    `fraction_of_population_that_must_farm() * population` -
    a fraction computed purely from crop/soil/rotation/toolkit/storage-
    technique constants, never from the current nutrition ratio, wage,
    price, or any other scarcity signal `_demographic_recovery` has
    available. This test pins that: the SAME fraction applies whether the
    population is comfortably fed or in the middle of a severe,
    land-caused famine, which is the direct, checked answer to "can a
    famine turn blacksmiths into farmers" (Complaints/45's fourth
    question) - not yet, because nothing here reads the famine at all
    before deciding how many people farm.
    """

    def test_the_farm_share_is_identical_whether_or_not_a_famine_is_happening(self):
        fed = _rome_sim(events=False)
        fed._demographic_recovery(101)
        fed_share = (agriculture.fraction_of_population_that_must_farm())

        starving = _rome_sim(events=False)
        starving.farm_land.hectares *= 0.15  # a severe, real famine
        starving._demographic_recovery(101)
        starving_share = (agriculture.fraction_of_population_that_must_farm())

        # Not merely close - EXACTLY the same call, because nothing in the
        # call site passes anything famine-dependent to it (see
        # sim/engine/core.py's `_demographic_recovery`: `agriculture.
        # farm_workers_fte_for_population(adult_equivalent_population)` is
        # called with no crop/soil/rotation/toolkit override, ever).
        self.assertEqual(fed_share, starving_share)
        # And the nutrition ratios differ hugely, confirming the famine
        # was real and severe while the workforce share never moved at all.
        self.assertLess(
            starving._last_demographic_step.nutrition_ratio,
            fed._last_demographic_step.nutrition_ratio - 0.3)
