"""What the spin-up reads of one hidden year, in one place for the run (spin_up_run.py) and the stage replay
(spin_up_stages.py): which goods are watched, the inputs each year steps with and the state a year is measured by."""
from sim.constants import declare
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs

from . import port_sites

SPIN_UP_WATCHED_GOODS = declare(
    "SPIN_UP_WATCHED_GOODS", 12, kind="temporary_heuristic", unit="goods", source=None, confidence="D", retire="Complaints/473",
    why="The spin-up reads whether prices have settled from the goods the opening basket spends most on; this many cover "
        "most of the spending, and a settled-ness test over every good would be dominated by thinly traded ones.")


def watched_goods_of(basket, prices, count):
    """The `count` goods of `basket` (quantity by good) with the largest spending at `prices` (a good with no price
    counts as spending nothing), largest first."""
    return sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:count]


def watched_goods(economy):
    """The goods the spin-up watches on `economy`: the opening basket's largest spending."""
    return watched_goods_of(economy_api.opening_quantities(economy), economy_api.opening_prices_of(economy),
                            int(SPIN_UP_WATCHED_GOODS))


def year_inputs(economy):
    """The inputs every hidden year steps with: no people placed from outside and no engine orders."""
    return EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy),
                             engine_orders={})


def year_state(quantities, price_level, rate, prices, watched):
    """The state of a year as spin_up_gap measures it: the settle `quantities` (economy_api.spin_up_state), the price
    level, the rate (None when the economy has none) and the prices of the `watched` goods that were priced."""
    return {**quantities, "price_level": price_level, "rate": rate,
            "prices": {good: prices[good] for good in watched if prices.get(good) is not None}}
