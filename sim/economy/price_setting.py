"""A seller's ask for the year, chosen as Eurace@Unibi's firm chooses its price (Market_Research/Firm_market_research_functions.c,
Firm_set_price): try a grid of prices around the current one, work out what each would earn over the year, take the best.

What a candidate price earns is the market's size times the share the seller expects at that price against the other
sellers' asks, sold month by month out of the stock it holds (sales never exceed the stock), at price less the cost of a
unit, each month discounted. The share is the household's logit (Market_Research/Household_Market_Research_Functions.c,
Household_respond_questionnaire, and Cons_Goods/Household_Consumer_Functions.c, Household_rank_and_buy_goods): the weight of
a seller is its price to the power of minus the intensity of choice, the share is its weight over the sum of weights.
Eurace estimates the share by asking a sample of households and fitting an exponential in price to their answers
(Firm_analyze_questionnaire); here the expected share is computed directly, since the sellers' asks are in the book.

A seller that has sold out keeps raising until its stock binds; a seller with a stock beyond what it expects to sell
sees no gain from asking more than the logit's markup; a seller with nothing to sell has no reason to move. Fixed costs
enter Eurace's earnings but not the choice among prices, so they are left out.
"""
import math
from typing import List, Sequence, Tuple

from sim.constants import declare

_RETIRE = "Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md"

LOGIT_INTENSITY = declare(
    "LOGIT_INTENSITY", 12.0, kind="temporary_heuristic", unit="exponent of a seller's price in a buyer's choice weight",
    source=None, confidence="D", retire=_RETIRE,
    why="Eurace@Unibi, Cons_Goods/Household_Consumer_Functions.c and Market_Research/Household_Market_Research_Functions.c "
        "weight a seller by exp(gamma_const * (gamma_quality * log quality - log price)); gamma_const is 12 in Eurace's "
        "initial state (its/0_after_2k_transient.xml) and quality is not modelled here. How sharply buyers go to the "
        "cheaper seller is a price sensitivity to derive from the buyers' own substitution, not a fixed figure.")
GRID_START = declare(
    "GRID_START", 0.8, kind="temporary_heuristic", unit="multiple of the current price: lowest price tried",
    source=None, confidence="D", retire=_RETIRE,
    why="Eurace@Unibi, Market_Research/Firm_market_research_functions.c (Firm_set_market_research_data_pricing) tries "
        "prices from mr_start_price times the current price, 0.8 in its initial state (its/0_after_2k_transient.xml). "
        "A seller decides once a year in Eurace as here, so the span is how far it moves in a year; a span derived "
        "from how fast buyers can be expected to notice and move is not built.")
GRID_END = declare(
    "GRID_END", 1.2, kind="temporary_heuristic", unit="multiple of the current price: the grid stops below this",
    source=None, confidence="D", retire=_RETIRE,
    why="Eurace@Unibi mr_end_price, 1.2 in its initial state (its/0_after_2k_transient.xml); the last price tried is "
        "the largest step below it, as in the C's integer count of steps.")
GRID_STEP = declare(
    "GRID_STEP", 0.01, kind="temporary_heuristic", unit="multiple of the current price between two prices tried",
    source=None, confidence="D", retire=_RETIRE,
    why="Eurace@Unibi mr_price_increment, 0.01 in its initial state (its/0_after_2k_transient.xml); a finer grid moves "
        "the answer by less than a step.")
MONTHLY_DISCOUNT_RATE = declare(
    "MONTHLY_DISCOUNT_RATE", 0.02, kind="temporary_heuristic", unit="per month, applied to the months of the year",
    source=None, confidence="D", retire=_RETIRE,
    why="Eurace@Unibi discont_rate, 0.02 in its initial state (its/0_after_2k_transient.xml), applied to the earnings of "
        "each month of the year (Firm_set_price). In a year of even sales it scales every candidate alike; it matters "
        "when the stock runs out part way, when earlier sales count for more.")
MONTHS = 12      # the year's months over which Firm_set_price spreads expected sales


def grid_prices(current: float) -> List[float]:
    """The prices tried: the current price times GRID_START, GRID_START + GRID_STEP, ... below GRID_END (Eurace@Unibi,
    Firm_set_market_research_data_pricing: the count of steps is the integer part of the span over the step)."""
    count = int((GRID_END - GRID_START) / GRID_STEP)
    return [current * (GRID_START + step * GRID_STEP) for step in range(count)]


def logit_share(price: float, rivals: Sequence[Tuple[float, float]], intensity: float = LOGIT_INTENSITY) -> float:
    """The share a seller asking `price` expects against `rivals` ((ask, count of sellers asking it) pairs): its weight
    over the sum of weights, a weight being the ask to the power of minus `intensity` (Eurace@Unibi, Household_respond_questionnaire,
    logit_denominator). Weights are taken relative to the seller's own price so a large intensity does not overflow."""
    own = 1.0
    others = math.fsum(count * math.exp(-intensity * math.log(ask / price)) for ask, count in rivals if ask > 0.0 and count > 0.0)
    return own / (own + others)


def expected_earnings(price: float, unit_value: float, expected_sales: float, stock: float) -> float:
    """The year's discounted earnings at `price` if `expected_sales` are wanted over the year, sold evenly by month out of
    `stock` (Eurace@Unibi, Firm_set_price: actual_sales_estimation = min(current_stocks, expected_sales) each month, earnings
    discounted by 1 / (1 + discont_rate) per month)."""
    total, left = 0.0, stock
    for month in range(MONTHS):
        sold = min(left, expected_sales / MONTHS)
        left -= sold
        total += sold * (price - unit_value) / (1.0 + MONTHLY_DISCOUNT_RATE) ** month
    return total


def best_price(current: float, unit_value: float, market_size: float, rivals: Sequence[Tuple[float, float]], stock: float,
               floor: float, ceiling: float, intensity: float = LOGIT_INTENSITY) -> float:
    """The price on the grid around `current`, kept between `floor` and `ceiling`, that earns most over the year
    (Eurace@Unibi, Firm_set_price: the first price with the highest estimated earnings; here a tie keeps the current price,
    so a seller whose sales are all capped by an empty stock does not move). `market_size` is the year's quantity bought
    from all sellers, `rivals` the other sellers' (ask, count of sellers) pairs, `stock` what the seller can sell."""
    best, best_earnings = current, expected_earnings(
        current, unit_value, market_size * logit_share(current, rivals, intensity), stock)
    for candidate in sorted({min(max(price, floor), ceiling) for price in grid_prices(current)}):
        if candidate <= 0.0:
            continue
        earnings = expected_earnings(candidate, unit_value, market_size * logit_share(candidate, rivals, intensity), stock)
        if earnings > best_earnings + 1e-12 * max(abs(best_earnings), 1e-300):
            best, best_earnings = candidate, earnings
    return best
