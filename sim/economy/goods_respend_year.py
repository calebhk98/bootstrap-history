"""The year's second round of household buying: after every market has cleared, a cohort rationed in some market bids
what it could not spend on the goods still offered (goods_respend.py), the markets clear again against the stock left,
and a cohort still rationed goes on until nothing more is bought. Money no offered good takes stays with the cohort.
All the rounds run in one kernel over every rationed cohort and market (goods_respend_kernel.py).
"""
from typing import Dict, Tuple

import numpy

from sim.constants import declare

from . import goods_respend_pack, goods_respend_unpack
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_respend import RESPEND_NEGLIGIBLE_ROUND_SHARE
from .goods_respend_kernel import respend_rounds
from sim.book import ROUNDING_SHARE

Market = Tuple[str, str]

RESPEND_APPORTIONED_WANTED_SHARE = declare(
    "RESPEND_APPORTIONED_WANTED_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the round's wanted counted for the bids that add demand",
    source=None, confidence="D",
    why="A respend round's clearing gives the demand of all its bids together; the part that is new demand is taken "
        "pro rata to the adding bids' demand at one price, not computed bid by bid at the asks each faced.",
    retire="Complaint 964 exact wanted quantity per bid")


class LeftMarket:
    """A cleared market as the second round finds it: its bids and first-round result, the offers with what sold taken
    off, its last price, what has been delivered in it, what its buyers wanted (`wanted_in_round`, summed over the
    rounds), the bids that add demand in each round (`bids_adding_demand`) and the clearings of every round. What is unsold is what the last round to
    clear it left on offer."""

    def __init__(self, bids, result, offers, last_price, delivered, wanted, idle_years=0, bought=None):
        self.delivered = delivered     # goods moved in all rounds so far
        self.wanted = wanted           # what buyers asked for in all rounds so far
        self.idle_years = idle_years   # years the market lacked bids or offers, before this year
        self.results = [result]
        self.bought = bought or {}     # buyer -> (units received, money paid) in the first round's settlement
        self.bids = bids
        self.all_bids = list(bids)     # the first round's bids and the later rounds' that add demand
        self.last_offered = result.offered_at_price     # on offer at the last round's price
        self.last_delivered = delivered                 # moved in the last round
        self.result = result
        self.offers = offers
        self.last_price = last_price

    @property
    def unsold(self) -> float:
        """What the last round to clear this market left on offer."""
        return max(0.0, self.last_offered - self.last_delivered)


def respend(setup, record, view, ledger, markets: Dict[Market, LeftMarket], basket_of) -> None:
    """Clear the households' leftover bids against the stock left in `markets`, in rounds, and settle them."""
    packed = goods_respend_pack.pack(setup, record, view, ledger, markets, basket_of)
    if packed is None:
        return
    out = run_rounds(packed)
    goods_respend_unpack.write_markets(setup, ledger, markets, packed, out)
    goods_respend_unpack.write_settlement(setup, record, ledger, packed, out)


CHANGED_BY_KERNEL = ("has_bid", "offer_quantity", "key_stock", "agent_cash")


def run_rounds(packed):
    """The kernel's answer for `packed`, run again with room for more rows while its logs are full. The arrays the kernel
    changes are copied for each run; those of the last run replace them in `packed.arguments`."""
    capacity = max(4096, 8 * len(packed.arguments["first_market"]))
    while True:
        arguments = {name: array.copy() if name in CHANGED_BY_KERNEL else array
                     for name, array in packed.arguments.items()}
        out = respend_rounds(*arguments.values(), RESPEND_APPORTIONED_WANTED_SHARE, RESPEND_NEGLIGIBLE_ROUND_SHARE,
                             MINIMUM_PRICE_SHARE_OF_REFERENCE, ROUNDING_SHARE, capacity)
        if not out[0]:
            packed.arguments = arguments
            return out
        capacity *= 4
