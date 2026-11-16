"""Numba port, labour clearing: the choice odds of workers weighing a switch (`switching_kernel.band_shares`) agree with the
plain per-band loop it replaced, on random scores; no game.

The kernel sums the logit weights left to right where the plain loop used `math.fsum`, so shares agree to a relative
tolerance. The shares are continuous in the scores, so a last-digit difference stays a last-digit difference."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy as np

from sim.tests.labour_switching_reference import band_odds

TOLERANCE = 1e-12
NEGLIGIBLE = 1e-3


def plain_band_odds(chances, gain, lost, subsistence, stay_score, scale, negligible):
    """Per band: None (it stays) or [(target position, share)]: every target weighed against staying, each share trimmed by
    `negligible` and the trimmed people spread over the others in proportion (`switching_kernel.band_shares`)."""
    bands = []
    for band in range(len(chances[0])):
        scores = [(chances[index][band] * gain[index] - lost[index]) / subsistence for index in range(len(gain))]
        top = max(scores + [stay_score])
        weights = [math.exp((score - top) / scale) for score in scores]
        total = math.fsum(weights + [math.exp((stay_score - top) / scale)])
        raw = [weight / total for weight in weights]
        trimmed = [share - negligible if share > negligible else 0.0 for share in raw]
        kept = math.fsum(trimmed)
        if kept <= 0.0:
            bands.append(None)
            continue
        spread = 1.0 + (math.fsum(raw) - kept) / (kept + negligible)
        bands.append([(index, share * spread) for index, share in enumerate(trimmed) if share > 0.0])
    return bands


class BandSharesAgreeWithThePlainLoop(unittest.TestCase):

    def test_random_scores(self):
        rng = random.Random(8)
        for _case in range(300):
            targets, bands = rng.randint(1, 7), rng.randint(1, 6)
            chances = [[rng.uniform(0.0, 1.0) for _band in range(bands)] for _target in range(targets)]
            gain = [rng.uniform(-2.0, 30.0) for _target in range(targets)]
            lost = [rng.uniform(0.0, 12.0) for _target in range(targets)]
            subsistence, stay_score = rng.uniform(0.5, 3.0), rng.choice([0.0, rng.uniform(-3.0, 3.0)])
            scale = rng.choice([1.0, rng.uniform(0.3, 2.0)])
            expected = plain_band_odds(chances, gain, lost, subsistence, stay_score, scale, NEGLIGIBLE)
            shares, moves = band_odds(chances, gain, lost, subsistence, stay_score, scale, NEGLIGIBLE)
            for band, plain in enumerate(expected):
                self.assertEqual(bool(moves[band]), plain is not None)
                if plain is None:
                    continue
                got = {index: share for index, share in enumerate(shares[band].tolist()) if share > 0.0}
                self.assertEqual(sorted(got), sorted(index for index, _share in plain))
                for index, share in plain:
                    self.assertAlmostEqual(got[index], share, delta=TOLERANCE)


if __name__ == "__main__":
    unittest.main()
