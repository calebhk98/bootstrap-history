"""A household's choice of how much to hold in shares, and the clearing house that matches the orders.

Follows Eurace@Unibi (ETACE/eurace_unibi, used with the authors' permission; see NOTICE.md):
- `fraction_to_invest` follows `logit_decision_model` in Financial/Household_aux_functions.c;
- `net_investment` follows `Household_revises_expected_portfolio` in Financial/Household_Financial_Market_Functions.c
  (steps 1, 3a, 4 and 5);
- `match_orders` follows `ClearingHouse_compute_transactions` in Financial/ClearingHouse_Financial_Market_Functions.c
  (aggregate demand and supply, then the long side is rationed by the ratio; with either side empty nothing trades);
- `next_price_factor` follows `ClearingHouse_update_price` in the same file (price times the demand over supply
  ratio to the power INDEX_PRICE_ADJ, held between INDEX_PRICE_ADJ_MIN and INDEX_PRICE_ADJ_MAX).
Differences: Eurace has one index of all firms with equal weights and a price in money per unit; here the index is
every producer's equity and its price is a factor on each producer's net worth (the factor is the index price,
starting at one). Eurace orders whole units and corrects rounding by random rationing; orders here are values. The
shipped state sets trading_random = 1 (a random fraction of the budget); this takes the logit branch
(trading_random = 0), which has no random draw. The C passes the index's moving-average price in the slot of the
expected return (a price against a rate); here the expected return is the dividend yield at the index price.
"""
import math
from typing import Dict, Mapping, Optional, Tuple

from sim.constants import declare

LOGIT_BETA = declare(
    "LOGIT_BETA", 2.96, kind="temporary_heuristic",
    unit="intensity of choice between deposits and shares (dimensionless)",
    source=(
        "Eurace@Unibi shipped state 0_after_2k_transient.xml (its/0_after_2k_transient.xml.tar.bz2, opened): "
        "logit_beta of the 1600 households ranges 1.00 to 5.00, mean 2.96; one value is used for every household here."),
    confidence="D",
    why="How strongly a household shifts its budget to the asset with the higher return. Not measured for any "
        "pre-modern society.",
    retire="Complaints/106: a household's choice of holdings from its own risk and horizon replaces the stored intensity")
INDEX_PRICE_ADJUSTMENT = declare(
    "INDEX_PRICE_ADJUSTMENT", 1.0, kind="temporary_heuristic", unit="exponent on the demand over supply ratio",
    source="Eurace@Unibi shipped state 0_after_2k_transient.xml (opened): index_price_adj 1.0. The manual (section 8.2) "
           "gives 0.5 as typical.", confidence="D",
    why="The speed at which the share price follows excess demand.",
    retire="Complaints/106: a price formed by a market maker's inventory or an auction replaces the adjustment speed")
INDEX_PRICE_ADJUSTMENT_MAX = declare(
    "INDEX_PRICE_ADJUSTMENT_MAX", 1.1, kind="temporary_heuristic", unit="largest rise of the share price in a year, as a ratio",
    source="Eurace@Unibi shipped state 0_after_2k_transient.xml (opened): index_price_adj_max 1.1. The C applies it "
           "monthly; here it limits a year.", confidence="D",
    why="A ceiling on the price's yearly rise.",
    retire="Complaints/106: a price formed by a market maker's inventory or an auction replaces the ceiling")
INDEX_PRICE_ADJUSTMENT_MIN = declare(
    "INDEX_PRICE_ADJUSTMENT_MIN", 0.9, kind="temporary_heuristic", unit="largest fall of the share price in a year, as a ratio",
    source="Eurace@Unibi shipped state 0_after_2k_transient.xml (opened): index_price_adj_min 0.9. The C applies it "
           "monthly; here it limits a year.", confidence="D",
    why="A floor under the price's yearly fall.",
    retire="Complaints/106: a price formed by a market maker's inventory or an auction replaces the floor")


def fraction_to_invest(risk_free_rate: float, expected_return: float, beta: float = None) -> Optional[float]:
    """The part of the portfolio budget put in shares: the Boltzmann (multi-logit) weight of the share's relative
    performance against the deposit's (Eurace `logit_decision_model`). None when the two performances do not sum to a
    positive number (the C prints an error there)."""
    beta = LOGIT_BETA if beta is None else beta
    total = risk_free_rate + expected_return
    if total <= 0.0:
        return None
    deposit_weight = math.exp(beta * risk_free_rate / total)
    share_weight = math.exp(beta * expected_return / total)
    return share_weight / (deposit_weight + share_weight)


def net_investment(fraction: float, savings: float, share_wealth: float) -> float:
    """The value to buy (positive) or sell (negative): the fraction of the portfolio budget (savings left after the
    planned consumption, plus the shares held) that is to be in shares, less the shares held (Eurace
    `Household_revises_expected_portfolio`). A sale is held to what is held (the C's step 5); a purchase is held to
    the savings, since a household here cannot overdraw (the C lets the payment account fall below zero)."""
    planned = fraction * (savings + share_wealth)
    net = planned - share_wealth
    return max(-share_wealth, min(savings, net))


def match_orders(orders: Mapping[str, float]) -> Tuple[Dict[str, float], float]:
    """(matched value per trader, demand over supply). Buyers' orders are positive, sellers' negative. The long
    side is cut by the ratio; with no buyer or no seller nothing trades and the ratio is one (Eurace
    `ClearingHouse_compute_transactions`)."""
    demand = sum(value for value in orders.values() if value > 0.0)
    supply = -sum(value for value in orders.values() if value < 0.0)
    if demand <= 0.0 or supply <= 0.0:
        return {trader: 0.0 for trader in orders}, 1.0
    ratio = demand / supply
    matched = {trader: (value / ratio if value > 0.0 and ratio > 1.0 else value * ratio if value < 0.0 and ratio < 1.0 else value)
               for trader, value in orders.items()}
    return matched, ratio


def next_price_factor(factor: float, ratio: float, adjustment: float = None, maximum: float = None,
                      minimum: float = None) -> float:
    """The index price after a year's trading (Eurace `ClearingHouse_update_price`)."""
    adjustment = INDEX_PRICE_ADJUSTMENT if adjustment is None else adjustment
    maximum = INDEX_PRICE_ADJUSTMENT_MAX if maximum is None else maximum
    minimum = INDEX_PRICE_ADJUSTMENT_MIN if minimum is None else minimum
    return max(minimum, min(maximum, ratio ** adjustment)) * factor


def share_wealth(parts: Mapping[str, float], worths: Mapping[str, float], factor: float) -> float:
    """What the parts a holder bought of each producer are worth at the index price."""
    return factor * sum(part * worths.get(producer, 0.0) for producer, part in parts.items())


def expected_yield(dividends: Mapping[str, float], prices: Mapping[str, float]) -> Optional[float]:
    """The dividends the index paid over its value; None when it has no value."""
    value = sum(prices.values())
    if value <= 0.0:
        return None
    return sum(dividends.get(producer, 0.0) for producer in prices) / value
