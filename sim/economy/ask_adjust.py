"""A seller's ask moves between years with its unsold stock against a target stock: stock below the target (sold
out) raises it, stock above the target cuts it, in proportion to the gap, and it stays inside the band around the
seller's unit cost (`band_edge` above, the cost that just covers a unit below). It follows the inventory side of
Eurace@Unibi's firm (Cons_Goods/Firm_Producer_Functions.c, Firm_calc_production_quantity: critical stock against
current stock), which Eurace's own price rule (Market_Research/Firm_market_research_functions.c, Firm_set_price)
reads only as a cap on expected sales. The search for unsold stock inside the year (unsold_search.py) is the other
half of the cut: this is the price the seller carries into next year. A seller whose stock is all gone but whose ask is
already a multiple of what a unit costs it learns nothing more by asking higher (ASK_BAND_CEILING), and a good whose
supply cannot respond does not climb for decades."""
import math
from typing import List, Optional

from sim.constants import declare

from . import inventory

GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR = declare(
    "GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="share of the expected price a seller moves it in a year when its stock is a whole target away from the target",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi firms move price in small steps toward the best of a grid of nearby prices (Firm_set_price), and "
        "Caiani et al. 2016 (eq 3.7) move the markup with inventory; the speed is a fixed stand-in for a seller that reads the "
        "slope of its own demand. A step proportional to the stock gap shrinks as the stock nears its target, which is what "
        "lets a cobweb settle; a fixed step either way does not. Raises that were too fast swung durable purchases "
        "(Complaint 468).")

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


def stock_gap(stock: float, target_stock: float) -> float:
    """How far a stock is from its target, as a share of the target clamped to [-1, 1]: one when nothing is held, minus
    one when a whole target is held beyond it. With no target, any stock at all is a full surplus."""
    if target_stock <= 0.0:
        return -1.0 if stock > 0.0 else 0.0
    return max(-1.0, min(1.0, (target_stock - stock) / target_stock))


def regressive_weight(weight: float, gap: float) -> float:
    """The share of the gap to cost a seller's expectation closes in a year, given its stock gap (`stock_gap`): the pull
    toward cost says a price above cost will not last because makers enter, which a seller that sold out with buyers
    unserved has evidence against. Full at or below its target stock, none when nothing is left."""
    return weight * (1.0 - max(0.0, min(1.0, gap)))


def adjusted_within_band(expected_price: float, break_even_price: Optional[float], stock: float, target_stock: float,
                         ceiling_multiple: float = ASK_BAND_CEILING, input_share: float = 0.0) -> float:
    """`expected_price` moved one step by the gap between `stock` and `target_stock`, inside the band: the price that just
    covers a unit's cost (`break_even_price`) below, `band_edge` above. A seller already outside the band on the side it
    is moving away from is left where it is, not pulled in here; one with no cost to anchor on does not move."""
    if break_even_price is None or not math.isfinite(break_even_price) or break_even_price <= 0.0:
        return expected_price
    moved = expected_price * (1.0 + GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR * stock_gap(stock, target_stock))
    if moved >= expected_price:
        return max(expected_price, min(moved, band_edge(break_even_price, input_share, ceiling_multiple)))
    return min(expected_price, max(moved, break_even_price))


def unsold_stock(producer, recipe, view, good: str) -> float:
    """What the producer holds of an output beyond its own runs' inputs of the same good."""
    return (view.stock(producer.agent_id, good, producer.tile) - recipe.inputs.get(good, 0.0) * producer.capacity_runs)


def target_of(producer, recipe, good: str) -> float:
    """The stock the producer's expected sales call for."""
    return inventory.target_stock(producer.expected_sales) * recipe.outputs[good]


def worked_outputs(producer, recipe) -> List[str]:
    """Outputs of a producer that worked last year; one that did not has no sales to read a stock against."""
    return sorted(recipe.outputs) if producer.last_runs > 0.0 else []
