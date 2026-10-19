"""Complaint 507, stage 4: in a run with no intervention every commodity's traded volume stays near its first settled
year's, so output per head stays near one; the volumes are the economy's own, not a second model's."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import close_years

from sim.economy import api as economy_api

YEARS = 4
# A commodity's volume drifts with the world's own year-to-year weather and stock; it does not move by multiples.
RATIO_BAND = 3.0
# Measured on rome_100ad over four years: at most 0.29 of the baseline value, in the third year, and 0.01 in the fourth.
MOVED_SHARE = 1.0 / 3.0

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
check("output per head is one in the baseline year", abs(per_head[0] - 1.0) <= 1e-9, per_head)
check("...and stays near one with no intervention", all(0.5 < each < 2.0 for each in per_head), per_head)
check("goods far from their baseline carry a small share of the basket", max(shares_moved) <= MOVED_SHARE, shares_moved)
