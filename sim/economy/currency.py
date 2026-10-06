"""Money regimes, minting and melting, issue, money demand and the price level.

Pure functions over `types.CurrencySpec`. Anything that moves money returns `Transfer` lists for the
caller to book; nothing here touches a book. The mint's market side is in mint.py.
"""
import dataclasses
from typing import Mapping, Optional

from sim.constants import declare

from . import types
from .types import AgentId, CurrencySpec, GoodId, Transfer

REGIMES = ("struck_coin", "weighed_metal", "commodity", "fiat")

BASE_HOLDING_YEARS = declare(
    "BASE_HOLDING_YEARS", 0.25, kind="temporary_heuristic", unit="years of spending",
    why="cash an agent holds when money costs nothing to hold, as years of spending; stands in for the "
        "velocity of money, which should come from payment-period timing of wages, rents and markets. "
        "Estimates of historical velocity would fix it.")

HOLDING_COST_ELASTICITY = declare(
    "HOLDING_COST_ELASTICITY", 4.0, kind="temporary_heuristic", unit="per unit of yearly holding cost",
    why="how sharply the holding period shrinks as interest plus expected inflation rises: "
        "holding = base / (1 + elasticity * cost). Chosen so hyperinflation expectations empty purses; "
        "to be fitted to inflation-versus-real-balance data from hyperinflation episodes.")

SPENDING_ADJUSTMENT_SHARE = declare(
    "SPENDING_ADJUSTMENT_SHARE", 0.5, kind="temporary_heuristic", unit="share of the cash gap per year",
    why="share of cash above (below) target that an agent spends (saves) within the year; a stock-adjustment "
        "speed with no source. Household panel data on windfall spending would fix it.")

EXPECTATION_ADJUSTMENT_SPEED = declare(
    "EXPECTATION_ADJUSTMENT_SPEED", 0.5, kind="temporary_heuristic", unit="share of the surprise per year",
    why="adaptive expectations: share of last year's forecast error taken up this year; standard "
        "modelling convention, no historical source for any period.")


def currency_from_coin_standard(civ_id: str, coin_standard: Mapping, currency_name: str,
                                issuer: Optional[AgentId] = None) -> CurrencySpec:
    """Read a civilisation's `coin_standard` block. Fields used: `regime` (one of REGIMES, required),
    `material`, `kg_per_unit`, and `mint_charge_share` (struck coin only: the share of the metal the
    issuer keeps for striking). A regime with no metal or commodity behind it must be fiat."""
    regime = coin_standard.get("regime")
    if regime not in REGIMES:
        raise ValueError("%s: coin_standard needs a regime, one of %s (got %r)" % (civ_id, ", ".join(REGIMES), regime))
    if regime == "fiat":
        return CurrencySpec(currency_name, "fiat", None, 0.0, issuer)
    material = coin_standard.get("material")
    per_unit = float(coin_standard.get("kg_per_unit") or 0.0)
    if not material or per_unit <= 0.0:
        raise ValueError("%s: %s money needs a material and kg_per_unit" % (civ_id, regime))
    charge = float(coin_standard.get("mint_charge_share", 0.0))
    if charge != 0.0 and regime != "struck_coin":
        raise ValueError("%s: only a struck coin has a mint charge, not %s" % (civ_id, regime))
    if not 0.0 <= charge < 1.0:
        raise ValueError("%s: mint_charge_share must be in [0, 1)" % civ_id)
    return CurrencySpec(currency_name, regime, material, per_unit, issuer if regime == "struck_coin" else None, charge)


def has_mint(spec: CurrencySpec) -> bool:
    """Only a struck coin has an issuer's mint; weighed metal and commodity money are exchanged with
    the metal or good at its weight, with no issuer and no charge."""
    return spec.regime == "struck_coin"


def mint_parity(spec: CurrencySpec) -> float:
    """Price in money of one unit of the backing good at which a unit of money is worth its metal."""
    return 1.0 / spec.backing_per_unit


def mint_price(spec: CurrencySpec) -> float:
    """Money the mint pays per unit of bullion: parity less the mint charge."""
    return (1.0 - spec.mint_charge_share) / spec.backing_per_unit


def issue(spec: CurrencySpec, amount: float, purpose: str) -> list:
    """Money created for the issuer: fiat, or coin struck beyond its metal."""
    if spec.issuer is None:
        raise ValueError("%s has no issuer" % spec.currency_id)
    if amount < 0.0:
        raise ValueError("amount must not be negative")
    return [Transfer(types.EDGE_ISSUE, spec.issuer, spec.currency_id, amount, purpose)]


def retire(spec: CurrencySpec, amount: float, purpose: str) -> list:
    """Money the issuer takes out of circulation (taxes burned, notes redeemed)."""
    if spec.issuer is None:
        raise ValueError("%s has no issuer" % spec.currency_id)
    if amount < 0.0:
        raise ValueError("amount must not be negative")
    return [Transfer(spec.issuer, types.EDGE_ISSUE, spec.currency_id, amount, purpose)]


def debase(spec: CurrencySpec, new_backing_per_unit: float) -> CurrencySpec:
    """The issuer strikes the same unit with a different amount of metal; the caller decides when."""
    if spec.regime != "struck_coin":
        raise ValueError("only a struck coin can be debased")
    if new_backing_per_unit <= 0.0:
        raise ValueError("a struck coin keeps some metal")
    return dataclasses.replace(spec, backing_per_unit=new_backing_per_unit)


def debase_by_cut(spec: CurrencySpec, cut_share: float, restrike_share: float) -> CurrencySpec:
    """The issuer cuts `cut_share` of the metal from the coin it strikes again, `restrike_share` of the
    stock this year: the average coin holds that share of the cut less metal. A coin that is not struck,
    or no cut, leaves the spec as it was."""
    if spec.regime != "struck_coin" or cut_share <= 0.0 or restrike_share <= 0.0:
        return spec
    return debase(spec, spec.backing_per_unit * (1.0 - cut_share * restrike_share))


def cash_balance_target(yearly_spending: float, interest_rate: float, expected_inflation: float) -> float:
    """Cash an agent wants to hold: a holding period of spending that falls as the cost of holding money
    (interest plus expected inflation) rises, and stays positive."""
    cost = max(0.0, interest_rate + expected_inflation)
    return yearly_spending * BASE_HOLDING_YEARS / (1.0 + HOLDING_COST_ELASTICITY * cost)


def spending_adjustment(cash: float, target: float, yearly_income: float) -> float:
    """Extra spending this year (negative: less) from cash above (below) target. Cutting back cannot
    exceed income; spending extra cannot exceed the cash."""
    change = SPENDING_ADJUSTMENT_SHARE * (cash - target)
    return max(-yearly_income, min(change, cash))


def update_expected_inflation(previous_expectation: float, observed_inflation: float) -> float:
    return previous_expectation + EXPECTATION_ADJUSTMENT_SPEED * (observed_inflation - previous_expectation)


def basket_price_level(prices_now: Mapping[GoodId, float], prices_base: Mapping[GoodId, float],
                quantities_base: Mapping[GoodId, float]) -> float:
    """Fixed-basket (base-quantity weighted) index; goods missing in any of the three are skipped."""
    now_cost = base_cost = 0.0
    for good, quantity in quantities_base.items():
        if good in prices_now and good in prices_base:
            now_cost += prices_now[good] * quantity
            base_cost += prices_base[good] * quantity
    return now_cost / base_cost if base_cost > 0.0 else 1.0


def exchange_rate(spec_from: CurrencySpec, spec_to: CurrencySpec,
                  backing_prices: Mapping[GoodId, float]) -> Optional[float]:
    """Units of `spec_to` money per unit of `spec_from`, at metal parity: the value of the metal in one
    unit of each, priced in a common numeraire by `backing_prices`. None if either is fiat (a floating
    rate is a later mechanism) or a backing price is missing."""
    values = []
    for spec in (spec_from, spec_to):
        if spec.backing_good is None:
            return None
        price = backing_prices.get(spec.backing_good)
        if not price or price <= 0.0:
            return None
        values.append(spec.backing_per_unit * price)
    return values[0] / values[1]
