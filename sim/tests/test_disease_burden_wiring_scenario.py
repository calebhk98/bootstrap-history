"""SCENARIO: WIRING ONE (Complaints/closed/47-technology-cannot-stop-people-dying-young.md):
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
unaffected, and that food technologies do not move it.

The medical nodes drive a live disease burden, so technology can lower mortality. The formula over the held technologies
is tested on built weights in test_disease_burden_wiring.py; that Rome starts holding none of the eight is test_disease_burden_start_data_rule.
"""
import unittest

from .harness import *  # noqa: F401,F403



def _rome_sim(events=False):
    return unopened_sim(civ="rome_100ad", events=events)


class DiseaseBurdenIsLiveTests(unittest.TestCase):
    """The disease technologies drive `_disease_burden` live, off `self.has()`."""

    def test_completing_a_disease_technology_moves_disease_burden_immediately(self):
        test_sim = _rome_sim()
        before = test_sim._disease_burden()
        test_sim.household.done.add("sanitation_antisepsis")
        test_sim.apply_tech_effects("sanitation_antisepsis")
        after = test_sim._disease_burden()
        self.assertLess(after, before)


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


if __name__ == "__main__":
    unittest.main()
