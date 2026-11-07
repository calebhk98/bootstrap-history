"""The choice odds of workers weighing a change of trade, for every ability band at once (the kernel behind
`switching._odds`).

A band scores each target trade by its chance of finishing the training times the gain, less the cost of the training;
an established worker considers only targets scoring above staying, the young consider all. Scores become logit weights
against staying; targets under a negligible share of the total are dropped and their weight goes to the leading target.
Sums run left to right."""
import numpy as np

from sim.jit import njit


@njit
def band_shares(chances, gain, lost, unit, stay_score, young, scale, negligible, shares):
    """Fill `shares[band, target]` (zero where a target is not picked or is dropped) and return, per band, whether the band
    moves at all. `chances[target, band]` is the chance of finishing, `gain` and `lost` are per target, scores are in units of `unit`
    (`stay_score` is already in them)."""
    count_targets = chances.shape[0]
    count_bands = chances.shape[1]
    moves = np.zeros(count_bands, np.bool_)
    scores = np.empty(count_targets)
    weights = np.empty(count_targets)
    for band in range(count_bands):
        picked = 0
        top = stay_score
        for target in range(count_targets):
            shares[band, target] = 0.0
            score = (chances[target, band] * gain[target] - lost[target]) / unit
            scores[target] = score
            if score > 0.0 or young:
                picked += 1
                if score > top:
                    top = score
        if picked == 0:
            continue
        total = 0.0
        heaviest = -1.0
        leader = -1
        for target in range(count_targets):
            if scores[target] > 0.0 or young:
                weights[target] = np.exp((scores[target] - top) / scale)
                total += weights[target]
                if weights[target] > heaviest:
                    heaviest = weights[target]
                    leader = target
            else:
                weights[target] = -1.0
        total += np.exp((stay_score - top) / scale)
        cutoff = total * negligible
        dropped = 0.0
        for target in range(count_targets):
            if weights[target] >= 0.0:
                if weights[target] >= cutoff:
                    shares[band, target] = weights[target] / total
                else:
                    dropped += weights[target]
        shares[band, leader] += dropped / total
        if shares[band, leader] < negligible:
            for target in range(count_targets):
                shares[band, target] = 0.0
            continue
        moves[band] = True
    return moves
