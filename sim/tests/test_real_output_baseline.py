"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 640), slow only. Not a rule test: it reads the whole Rome economy.

Relationship validated: in a run with no intervention a commodity's traded volume stays within a band of its first
year's, so output per head stays near one (Complaint 507, stage 4). The band is a declared temporary heuristic
(below), not a sourced figure. While the opening does not settle (Complaint 473) most of the basket's value moves
by more than the band in the first years, and the last check fails with that message; that failure is honest, so
the band is not loosened. The rule that real output is the sum of volumes times opening prices is in test_real_output."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import close_years

from sim.economy import api as economy_api

YEARS = 4
# A commodity's volume drifts with the world's own year-to-year weather and stock; it does not move by multiples.
# TEMPORARY HEURISTIC (retire Complaints/473, the unsettled spin-up): in a settled economy with no intervention a good
# is "far from one" beyond a factor of two of its baseline year, and goods that far carry a tenth of the baseline value
# at most. Stated from the subject, not fitted to a run; the unsettled opening may break it (Complaints/558).
RATIO_BAND = 2.0
MOVED_SHARE = 0.1

game = sim(civ="rome_100ad", capital=1e9)
check("the economy's opening basket is not empty", bool(economy_api.opening_quantities(game.economy.agent.economy())))
per_head = []
shares_moved = []
for _year in range(YEARS):
    close_years(game, 1)
    per_head.append(game.real_output_per_head())
    traded, _scale = game.traded_measure()
    basket = game.base_basket()
    baseline = game.economy.agent.stored["volume_baseline"]
    weight = {good: baseline[good] * basket["prices"][good] for good in traded}
    # the share of the baseline year's traded value carried by goods now far from their baseline volume
    shares_moved.append(sum(weight[good] for good in traded
                            if not 1.0 / RATIO_BAND <= traded[good] / baseline[good] <= RATIO_BAND) / sum(weight.values()))
print("MEASURE per head", [round(each, 3) for each in per_head], "share far", [round(each, 3) for each in shares_moved])
check("validation: output per head is one in the baseline year", abs(per_head[0] - 1.0) <= 1e-9, per_head)
check("validation: ...and stays near one with no intervention", all(0.5 < each < 2.0 for each in per_head), per_head)
check("validation: goods far from their baseline carry a small share of the basket (fails while the economy does not "
      "settle, Complaint 473)", max(shares_moved) <= MOVED_SHARE, shares_moved)
