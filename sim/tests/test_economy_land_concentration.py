"""BASELINE VALIDATION: land concentration after a century of harvest shocks, borrowing, default and partible
inheritance stays within the range measured pre-industrial societies show (CLAUDE.md 4.2). A validation of a
distribution over an ensemble of shock histories, not a target the model aims at.

The economy is the land fixture village (sim/tests/land_fixture.py): households that borrow against their plots
and default after a run of failed harvests, so titles move (the earlier check ran the opening economy, where nobody
defaulted, and passed on the opening's own Gini). The shock rate and length are scenario inputs, not outcomes.
The band is the sourced table in sim/economy/titles_concentration.py by denominator; Han China and the Mexica have
no band. No source gives a land top-decile share, so it is printed only.
"""
import random
import statistics
import unittest

from sim.economy import titles, titles_concentration
from sim.tests import land_fixture as fixture

HOUSEHOLDS = 20
YEARS = 100
SEEDS = range(8)
SPELL_START_CHANCE = 0.02           # per household and year: a run of failed harvests begins
SPELL_YEARS = 3                     # a run of failed harvests lasts this long (single bad years are borrowed through)
LANDLESS_SHARE_FOR_WIDE_BAND = 0.05  # the landless-counted rows assume a large landless share; below this they do not apply


def one_history(seed):
    """(summary at the end, the most land the lender held) for one shock history, partible inheritance on."""
    setup, record = fixture.village(HOUSEHOLDS, lender_is_a_household=True)
    lender = fixture.household_ids(record)[-1]
    rng, spell = random.Random(seed), {}

    def income(household, year):
        if household == lender:
            return fixture.NORMAL_INCOME
        left = spell.get(household, 0)
        if left == 0 and rng.random() < SPELL_START_CHANCE:
            left = SPELL_YEARS
        spell[household] = max(0, left - 1)
        return fixture.FAILED_INCOME if left > 0 else fixture.NORMAL_INCOME

    peak = [0.0]
    fixture.run(setup, record, YEARS, income, inheritance=True, lender=lender,
                on_year=lambda year: peak.__setitem__(0, max(peak[0], titles.holding(record, fixture.TILE, lender))))
    return titles_concentration.summary(setup.tiles, record), peak[0] - record.cohorts[lender].ownership_share


class LandGiniBandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.histories = [one_history(seed) for seed in SEEDS]
        print("land concentration after %d years, by shock history (gini landholders only, gini all households, "
              "landless share, top decile share): %s" % (YEARS, [
                  (round(row["gini_landholders_only"], 2), round(row["gini"], 2), round(row["landless_share"], 2),
                   round(row["top_decile_share"], 2)) for row, _ in cls.histories]))

    def test_the_ensemble_is_not_vacuous_the_lender_took_land_in_every_history(self):
        for _row, gathered in self.histories:
            self.assertGreater(gathered, titles.EPSILON)

    def test_the_median_land_gini_is_inside_the_sourced_band_for_its_denominator(self):
        rows = [row for row, _ in self.histories]
        wide = statistics.median(row["landless_share"] for row in rows) >= LANDLESS_SHARE_FOR_WIDE_BAND
        denominator = titles_concentration.LANDLESS_COUNTED if wide else titles_concentration.LANDHOLDERS_ONLY
        measured = statistics.median(row["gini" if wide else "gini_landholders_only"] for row in rows)
        low, high = titles_concentration.band(denominator)
        print("median land gini %.3f, %s band %.3f to %.3f" % (measured, denominator, low, high))
        self.assertGreaterEqual(measured, low)
        self.assertLessEqual(measured, high)

    def test_han_china_and_the_mexica_have_no_band(self):
        self.assertEqual(titles_concentration.NO_LAND_BAND, ("han_china", "mexica"))
        self.assertIsNone(titles_concentration.band(titles_concentration.LANDHOLDERS_ONLY, ("han_china", "mexica")))


if __name__ == "__main__":
    unittest.main()
