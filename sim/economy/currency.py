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

EXPECTATION_ADJUSTMENT_SPEED = declare(
    "EXPECTATION_ADJUSTMENT_SPEED", 0.5, kind="temporary_heuristic", unit="share of the surprise per year",
    why="adaptive expectations: share of last year's forecast error taken up this year; standard "
        "modelling convention, no historical source for any period.")


def currency_from_coin_standard(civ_id: str, coin_standard: Mapping, currency_name: str,
                                issuer: Optional[AgentId] = None) -> CurrencySpec:
    """Read a civilisation's `coin_standard` block. Fields used: `regime` (one of REGIMES, required),
    `material`, `kg_per_unit` (of the fine metal), `fineness` (struck coin only: the share of the coin's
    mass that is that metal, default 1) and `mint_charge_share` (struck coin only: the share of the metal
    the issuer keeps for striking). A regime with no metal or commodity behind it must be fiat."""
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
    fineness = float(coin_standard.get("fineness", 1.0))
    if fineness != 1.0 and regime != "struck_coin":
        raise ValueError("%s: only a struck coin has a fineness, not %s" % (civ_id, regime))
    if not 0.0 < fineness <= 1.0:
        raise ValueError("%s: fineness must be above 0 and at most 1" % civ_id)
    return CurrencySpec(currency_name, regime, material, per_unit, issuer if regime == "struck_coin" else None,
                        charge, fineness)


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
    # the coin keeps its weight, so less metal in it is a lower fineness
    return dataclasses.replace(spec, backing_per_unit=new_backing_per_unit,
                               fineness=spec.fineness * new_backing_per_unit / spec.backing_per_unit)


def units_struck_by_cut(spec: CurrencySpec, supply: float, cut_share: float, restrike_share: float) -> float:
    """Coin the issuer gains by striking the part of the stock that comes to the mint (`restrike_share` of
    `supply`) at `cut_share` less metal: the metal saved makes more coin of the lighter weight. Zero for a
    coin that is not struck, or no cut."""
    if spec.regime != "struck_coin" or spec.issuer is None or cut_share <= 0.0 or restrike_share <= 0.0:
        return 0.0
    return supply * restrike_share * cut_share / (1.0 - cut_share)


def debase_by_cut(spec: CurrencySpec, supply: float, cut_share: float, restrike_share: float) -> CurrencySpec:
    """The coin after that recoinage: the same metal spread over the coin there was and the coin struck from
    the saving, so the average coin holds less of it. A coin that is not struck, or no cut, is as it was."""
    struck = units_struck_by_cut(spec, supply, cut_share, restrike_share)
    if struck <= 0.0:
        return spec
    return debase(spec, spec.backing_per_unit * supply / (supply + struck))


def update_expected_inflation(previous_expectation: float, observed_inflation: float) -> float:
    return previous_expectation + EXPECTATION_ADJUSTMENT_SPEED * (observed_inflation - previous_expectation)


def price_inflation(prices_now: Mapping[GoodId, float], prices_before: Mapping[GoodId, float],
                    weights: Mapping[GoodId, float]) -> Optional[float]:
    """The yearly rise in prices as the weighted median of the goods' price changes, so a few thin goods whose prices
    run away do not set what households and lenders expect (a fixed-basket index follows them). `weights` are the
    goods' shares of spending; a good without a price in both years or without weight is left out. None when no
    good is left to compare."""
    rows = sorted((prices_now[good] / prices_before[good], weight) for good, weight in weights.items()
                  if weight > 0.0 and prices_now.get(good, 0.0) > 0.0 and prices_before.get(good, 0.0) > 0.0)
    if not rows:
        return None
    half = sum(weight for _relative, weight in rows) / 2.0
    reached = 0.0
    for relative, weight in rows:
        reached += weight
        if reached >= half:
            return relative - 1.0
    return rows[-1][0] - 1.0


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
