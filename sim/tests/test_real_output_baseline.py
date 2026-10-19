"""Complaint 507, stage 4: in a run with no intervention every commodity's traded volume stays near its first settled
year's, so output per head stays near one; the volumes are the economy's own, not a second model's."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import close_years

from sim.economy import api as economy_api

YEARS = 4
# A commodity's volume drifts with the world's own year-to-year weather and stock; it does not move by multiples.
RATIO_BAND = 3.0

game = sim(civ="rome_100ad", capital=1e9)
check("the economy's opening basket is not empty", bool(economy_api.opening_quantities(game.economy.agent.economy())))
per_head = []
worst = 1.0
for _year in range(YEARS):
    close_years(game, 1)
    per_head.append(game.real_output_per_head())
    baseline = game.economy.agent.stored["volume_baseline"]
    volumes = economy_api.traded_volumes(game.economy.agent.economy())
    for good in game.base_basket()["units"]:
        if baseline.get(good, 0.0) > 0.0:
            ratio = volumes.get(good, 0.0) / baseline[good]
            worst = max(worst, ratio, 1.0 / ratio if ratio > 0.0 else float("inf"))
check("output per head is one in the baseline year", abs(per_head[0] - 1.0) <= 1e-9, per_head)
check("...and stays near one with no intervention", all(0.5 < each < 2.0 for each in per_head), per_head)
check("no commodity's volume is far from its baseline", worst <= RATIO_BAND, worst)
