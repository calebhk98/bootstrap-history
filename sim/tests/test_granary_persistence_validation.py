"""Baseline validation (CLAUDE.md 4.2, Complaint 44): an unshocked rome_100ad century lands well above the 21.9 percent of
start the missing granary produced, and is fed near subsistence. Slow-only; the granary rules are in test_granary_persistence.py.

These bounds are loose on purpose: the baseline is allowed to be imperfect, and must never be forced flat by tuning a
physical quantity. A failure means the granary went inert or the double-seed deduction returned (Complaint 44)."""
import statistics
import unittest

from .harness import *  # noqa: F401,F403


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class CenturyMeasurementTests(unittest.TestCase):
    """The actual number Complaints/44 is about. Loose bounds, deliberately
    - see CLAUDE.md SS3.2: the baseline is not required to be flat, and
    must never be forced flat by tuning a physical quantity (this test
    would not catch that kind of cheat anyway; hand review is what
    guards against it). What this DOES guard is the
    granary regressing back to inert (a fresh `Storage(stock_kg=0.0, ...)`
    built every year again) or the double-seed-deduction bug returning,
    either of which would drag the century-end fraction back down toward
    Complaints/44's original 21.9%, or below it.
    """

    def test_unshocked_century_lands_well_above_the_pre_fix_measurement(self):
        test_sim = _rome_sim(events=False)
        start = test_sim.population.total
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
        end = test_sim.population.total
        fraction = end / start
        # Complaints/44's own pre-fix measurement was 0.219 (21.9%); this
        # task's own re-measurement on this checkout, before the granary
        # existed, was 0.195. Comfortably above either, without demanding
        # anything close to 1.0.
        self.assertGreater(fraction, 0.5, ("baseline validation, Complaint 44", start, end, fraction))

    def test_mean_nutrition_ratio_is_close_to_one_not_merely_plausible(self):
        # A tighter bound than test_agriculture_wiring.py's own
        # NoFamineWithoutCauseTests (which predates the granary and only
        # asks for > 0.7) - the granary's whole point is to bring this
        # closer to subsistence than the unbuffered wiring could.
        test_sim = _rome_sim(events=False)
        ratios = nutrition_ratios_over_years(test_sim, range(101, 201))
        mean_ratio = statistics.fmean(ratios)
        self.assertGreater(mean_ratio, 0.9, ("baseline validation, Complaint 44", ratios))
        # THE UPPER BOUND IS NOT 1.0: capping the mean at subsistence would
        # forbid the outcome this whole milestone is for. A population that
        # grows must, on average, be fed at or above subsistence - that is
        # what growth IS. With weather drawn per home region and pooled by
        # land share (Complaints/46), good years survive often enough to
        # show up in the mean, measured at 1.0042 over this century. The
        # band is comfortably fed, not gorging - the physical ceiling on
        # that is MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE (1.75), and a mean
        # anywhere near it would mean the farm is badly oversized.
        self.assertLess(mean_ratio, 1.1, ("baseline validation, Complaint 44", ratios))




if __name__ == "__main__":
    unittest.main()
