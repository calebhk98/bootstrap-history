"""A seller that sells out raises its ask; the half of the rule whose other half is the search for unsold
stock inside the year (unsold_search.py). It raises until the ask is high enough that some stock goes
unsold, where the search takes over, or until it reaches the edge of the band around its unit cost
(ASK_BAND_CEILING), where it stops: a seller whose stock is all gone but whose ask is already a multiple of
what a unit costs it learns nothing more by asking higher, and a good whose supply cannot respond does not
climb for decades."""
import math
from typing import List, Optional

from sim.constants import declare

from . import inventory

SOLD_OUT_ASK_RAISE_SHARE = declare(
    "SOLD_OUT_ASK_RAISE_SHARE", 0.05, kind="temporary_heuristic",
    unit="share of the expected price a seller adds in a year it sold everything it had", source=None,
    confidence="D",
    why="A seller with nothing left learns only that its ask was no higher than buyers would pay, not by how "
        "much, so it tries a little more. Smaller than the markdown of unsold stock because a raise that "
        "overshoots costs a year of sales while a cut that overshoots costs only margin; raises that were "
        "too fast swung durable purchases (Complaint 468).")
ASK_BAND_CEILING = declare(
    "ASK_BAND_CEILING", 3.0, kind="temporary_heuristic",
    unit="multiple of a unit's cost that bounds a seller's ask above when buyers' substitution does not",
    source=None, confidence="D", retire="Complaints/643-a-seller-facing-inelastic-demand-has-an-unbounded-ask.md",
    why="Lengnick 2013 (eq 8-9) holds each firm's price between two multiples of its marginal cost and Caiani "
        "et al. 2016 (eq 3.6-3.7) set it as a markup on expected unit cost, so no seller's ask is unbounded. "
        "Where buyers substitute toward other goods the band's width is derived (substitution_markup in "
        "seller_offers.py); where they do not, a width from the seller's cost structure (the buyers' cheapest "
        "alternative way to meet the need, priced from the recipes) is not yet built, so a stated multiple stands in.")


def band_edge(break_even_price: float, input_share: float = 0.0, ceiling_multiple: float = ASK_BAND_CEILING) -> float:
    """The top of the band: the multiple applies to what the seller adds (its labour, rent and plant), and the inputs it
    buys pass through at their cost. A multiple of the whole unit cost would compound along a chain of makers, each
    marking up inputs already marked up (a multiple to the power of the stages); this adds one multiple of each
    stage's own cost, so a chain's ceiling grows by a sum."""
    share = min(1.0, max(0.0, input_share))
    return break_even_price * (share + ceiling_multiple * (1.0 - share))


def raised_within_band(expected_price: float, break_even_price: Optional[float], ceiling_multiple: float = ASK_BAND_CEILING,
                       input_share: float = 0.0) -> float:
    """`expected_price` raised one step for a sold-out seller, stopping at the band's edge (`band_edge`): the price
    that just covers a unit's cost (`break_even_price`), `input_share` of which is bought inputs. A seller already
    above the edge is left where it is, not cut here (unsold stock does that); one with no cost to anchor on does
    not raise."""
    if break_even_price is None or not math.isfinite(break_even_price) or break_even_price <= 0.0:
        return expected_price
    edge = band_edge(break_even_price, input_share, ceiling_multiple)
    return max(expected_price, min(expected_price * (1.0 + SOLD_OUT_ASK_RAISE_SHARE), edge))


def sold_out_outputs(producer, recipe, view) -> List[str]:
    """Outputs of a producer that worked last year and holds nothing beyond its own runs' inputs and the
    working stock its sales call for: everything it offered sold at its ask."""
    if producer.last_runs <= 0.0:
        return []
    sold = []
    for good in sorted(recipe.outputs):
        spare = (view.stock(producer.agent_id, good, producer.tile)
                 - recipe.inputs.get(good, 0.0) * producer.capacity_runs
                 - inventory.target_stock(producer.expected_sales) * recipe.outputs[good])
        if spare <= 0.0:
            sold.append(good)
    return sold
