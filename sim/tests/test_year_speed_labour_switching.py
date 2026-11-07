"""Numba port, labour clearing: the choice odds of workers weighing a switch (`switching_kernel.band_shares`) agree with the
plain per-band loop it replaced, on random scores; no game.

The kernel sums the logit weights left to right where the plain loop used `math.fsum`, so shares agree to a relative
tolerance. A band whose leading destination sits on the negligible-share cutoff could go either way on a last-digit
difference, so cases are drawn from scores far from it."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy as np

from sim.labour.market import switching_kernel

TOLERANCE = 1e-12
NEGLIGIBLE = 1e-3


def plain_band_odds(chances, gain, lost, subsistence, stay_score, young, scale, negligible):
    """Per band: None (it stays) or [(target position, share)]: the loop `switching._odds` ran before the kernel."""
    bands = []
    for band in range(len(chances[0])):
        scores, picked = [], []
        for index in range(len(gain)):
            score = (chances[index][band] * gain[index] - lost[index]) / subsistence
            if score > 0.0 or young:
                scores.append(score)
                picked.append(index)
        if not scores:
            bands.append(None)
            continue
        top = max(scores + [stay_score])
        weights = [math.exp((score - top) / scale) for score in scores]
        total = math.fsum(weights + [math.exp((stay_score - top) / scale)])
        cutoff = total * negligible
        leader = weights.index(max(weights))
        shares = [weight / total if weight >= cutoff else 0.0 for weight in weights]
        shares[leader] += math.fsum(weight for weight in weights if weight < cutoff) / total
        if shares[leader] < negligible:
            bands.append(None)
            continue
        bands.append([(index, share) for index, share in zip(picked, shares) if share > 0.0])
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
            young, scale = rng.random() < 0.5, rng.choice([1.0, rng.uniform(0.3, 2.0)])
            expected = plain_band_odds(chances, gain, lost, subsistence, stay_score, young, scale, NEGLIGIBLE)
            shares = np.empty((bands, targets))
            moves = switching_kernel.band_shares(np.array(chances), np.array(gain), np.array(lost), subsistence, stay_score,
                                                 young, scale, NEGLIGIBLE, shares)
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
