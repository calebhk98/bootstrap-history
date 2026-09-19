"""WIRING ONE (Complaints/48-technology-cannot-stop-people-dying-young.md):
does the engine actually pass a disease burden to sim/world/demography.py,
or does every game still run at PRE_INDUSTRIAL_DISEASE_BURDEN forever while
the eight medical entries in _TECH_EFFECTS.json do nothing?

sim/tests/test_demography.py already proves the MODEL correct in isolation
(disease_burden moves mortality/fertility the right way, monotonically,
bounded - see its own DiseaseAndSanitationTests). This module is the seam
test that class cannot be: it builds a real `Sim` (sim/tests/harness.py) and
checks that completing one of the eight named technologies actually lowers
`Sim._disease_burden()`, that the lowered burden actually reaches
`Population.step` through `Sim._demographic_recovery`, that a civilisation
holding none of the eight (Rome, at the start of the game) is provably
unaffected, and that the food-effect technologies sharing _TECH_EFFECTS.
json's `population` field with the eight disease ones are excluded by
construction rather than by accident.
"""
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine.core import demography


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class DiseaseBurdenDefaultTests(unittest.TestCase):
    """Rome's starting_techs (data/civilizations/rome_100ad.json) hold none
    of Sim.DISEASE_BURDEN_TECH_IDS - checked directly here rather than
    assumed, because the whole point of this wiring only being a no-op on
    the unshocked baseline century depends on this being true.
    """

    def test_rome_starts_with_none_of_the_eight_disease_technologies(self):
        test_sim = _rome_sim()
        held = [tech_id for tech_id in test_sim.DISEASE_BURDEN_TECH_IDS
                if test_sim.has(tech_id)]
        self.assertEqual(held, [], held)

    def test_disease_burden_is_pre_industrial_by_default(self):
        test_sim = _rome_sim()
        self.assertEqual(test_sim._disease_burden(),
                          demography.PRE_INDUSTRIAL_DISEASE_BURDEN)


class DiseaseBurdenRespondsToUnlockedTechnologyTests(unittest.TestCase):
    """The formula itself: `1.0 - unlocked_weight / total_weight`, summed
    only over Sim.DISEASE_BURDEN_TECH_IDS - checked against
    _TECH_EFFECTS.json's own numbers rather than a re-typed constant, so a
    future reweighting of that file is still checked correctly.
    """

    def test_holding_one_technology_lowers_burden_by_exactly_its_own_share(self):
        from sim.engine.core import TECH_EFFECTS
        test_sim = _rome_sim()
        total_weight = sum(TECH_EFFECTS[tech_id]["population"]
                           for tech_id in test_sim.DISEASE_BURDEN_TECH_IDS)
        test_sim.household.done.add("germ_theory")
        expected = 1.0 - TECH_EFFECTS["germ_theory"]["population"] / total_weight
        self.assertAlmostEqual(test_sim._disease_burden(), expected, places=12)

    def test_holding_all_eight_reaches_fully_modern_disease_burden(self):
        test_sim = _rome_sim()
        for tech_id in test_sim.DISEASE_BURDEN_TECH_IDS:
            test_sim.household.done.add(tech_id)
        self.assertEqual(test_sim._disease_burden(), 0.0)

    def test_food_effect_technologies_do_not_move_disease_burden_at_all(self):
        # crop_rotation, fud_three_field_rotation, fud_seed_drill,
        # mat_newworld_crops and ag2_canning all carry a `population` field
        # in _TECH_EFFECTS.json too - CALORIES, not disease. Holding every
        # one of them must not move _disease_burden by so much as a bit,
        # because _disease_burden only ever sums DISEASE_BURDEN_TECH_IDS.
        test_sim = _rome_sim()
        food_effect_techs = ("crop_rotation", "fud_three_field_rotation",
                              "fud_seed_drill", "mat_newworld_crops", "ag2_canning")
        for tech_id in food_effect_techs:
            test_sim.household.done.add(tech_id)
        self.assertEqual(test_sim._disease_burden(),
                          demography.PRE_INDUSTRIAL_DISEASE_BURDEN)

    def test_burden_is_clamped_to_zero_one(self):
        test_sim = _rome_sim()
        for tech_id in test_sim.DISEASE_BURDEN_TECH_IDS:
            test_sim.household.done.add(tech_id)
        burden = test_sim._disease_burden()
        self.assertGreaterEqual(burden, 0.0)
        self.assertLessEqual(burden, 1.0)


class DiseaseBurdenIsLiveNotQueuedTests(unittest.TestCase):
    """The eight disease technologies drive `_disease_burden` LIVE, off
    `self.has()`, rather than feeding `_pop_tech_pending` (apply_tech_effects,
    society.py) like every other `population`-carrying entry and ramping into
    `_pop_scale_base` over POP_TECH_RAMP_YEARS - a path WIRING_MILESTONE_4.md
    SS1.3 already established is read by nothing, so queuing these eight
    there as well would have the same tree-author weight doing two jobs at
    once for no reason. The five FOOD-effect technologies are untouched and
    still queue as normal.
    """

    def test_completing_a_disease_technology_does_not_queue_pop_tech_pending(self):
        test_sim = _rome_sim()
        test_sim.household.done.add("germ_theory")
        test_sim.apply_tech_effects("germ_theory")
        self.assertEqual(test_sim._pop_tech_pending, [])

    def test_completing_a_disease_technology_moves_disease_burden_immediately(self):
        test_sim = _rome_sim()
        before = test_sim._disease_burden()
        test_sim.household.done.add("sanitation_antisepsis")
        test_sim.apply_tech_effects("sanitation_antisepsis")
        after = test_sim._disease_burden()
        self.assertLess(after, before)

    def test_completing_a_food_technology_still_queues_pop_tech_pending(self):
        test_sim = _rome_sim()
        test_sim.household.done.add("crop_rotation")
        test_sim.apply_tech_effects("crop_rotation")
        self.assertEqual(len(test_sim._pop_tech_pending), 1)


class DiseaseBurdenReachesPopulationStepTests(unittest.TestCase):
    """The actual seam: `_demographic_recovery` must pass `_disease_burden()`
    through to `self.population.step`, not merely compute it and let it sit
    unused. Checked by holding the harvest identical between two otherwise-
    identical sims (both forced onto the OLD single-region-style draw, see
    `_compute_farm_region_weights` monkeypatch below, so WIRING TWO's own
    region pooling cannot be the thing that makes them differ) and observing
    that only DEATHS differ once one of the two civilisations holds every
    disease technology.
    """

    def _no_region_pooling_sim(self):
        test_sim = _rome_sim()
        # Isolates WIRING ONE: forces the pre-WIRING-TWO single civilisation-
        # wide weather draw, so both sims built this way see IDENTICAL
        # weather (same civ id, same year -> same seed) and any DIFFERENCE
        # in their trajectories can only be attributed to disease_burden.
        test_sim._farm_region_weights = []
        return test_sim

    def test_modern_disease_burden_lowers_deaths_for_an_identical_harvest(self):
        baseline = self._no_region_pooling_sim()
        modern = self._no_region_pooling_sim()
        for tech_id in modern.DISEASE_BURDEN_TECH_IDS:
            modern.household.done.add(tech_id)

        baseline._demographic_recovery(101)
        modern._demographic_recovery(101)

        self.assertEqual(
            baseline._last_farm_year.food_available_kcal_per_day,
            modern._last_farm_year.food_available_kcal_per_day,
            "the two sims must see the identical harvest for this to isolate "
            "disease_burden alone")
        self.assertLess(modern._last_demographic_step.deaths,
                         baseline._last_demographic_step.deaths)

    def test_unshocked_century_is_unaffected_for_a_civilisation_holding_none_of_the_eight(self):
        # Rome holds none of DISEASE_BURDEN_TECH_IDS and this scenario is
        # manual (no autopilot ever starts a project - see harness.sim's own
        # default), so no technology of any kind completes over the run:
        # WIRING ONE must be a complete no-op on this specific measurement,
        # confirmed bit-for-bit against the same run with `_disease_burden`
        # forced to the pre-industrial default throughout.
        with_wiring = _rome_sim()
        without_wiring = _rome_sim()
        without_wiring._disease_burden = lambda: demography.PRE_INDUSTRIAL_DISEASE_BURDEN
        for year in range(101, 151):
            with_wiring._demographic_recovery(year)
            without_wiring._demographic_recovery(year)
        self.assertEqual(with_wiring.population.children, without_wiring.population.children)
        self.assertEqual(with_wiring.population.working_age, without_wiring.population.working_age)
        self.assertEqual(with_wiring.population.elderly, without_wiring.population.elderly)


if __name__ == "__main__":
    unittest.main()
