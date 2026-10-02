"""Money regimes, minting and melting, issue, money demand and the price level.

Pure functions over `types.CurrencySpec`. Anything that moves money or goods returns `Transfer` and
`GoodsMove` lists for the caller to book; nothing here touches a book.
"""
import dataclasses
from typing import Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import types
from .types import AgentId, CurrencySpec, GoodId, GoodsMove, Transfer

REGIMES = ("struck_coin", "weighed_metal", "commodity", "fiat")

# Used only when the civilisation data names no regime: whether a backing material is a metal.
METAL_MATERIAL_NAMES = declare(
    "METAL_MATERIAL_NAMES", ("gold", "silver", "copper", "bronze", "brass", "iron", "tin", "lead", "electrum"),
    kind="temporary_heuristic", unit="material names",
    why="coin_standard data has no regime field, so a struck or weighed metal is told from a commodity "
        "money by its material name; replaced by an explicit regime field in the civilisation data.")

ARBITRAGE_SPEED = declare(
    "ARBITRAGE_SPEED", 0.5, kind="temporary_heuristic", unit="share of holdings per unit of relative gap per year",
    why="holders bring metal to the mint or melt coin in proportion to the relative gap between bullion's "
        "price and the mint's terms; the real rate depends on mint access and transport, unmodelled here. "
        "A mint ledger of coin struck against bullion price would fix it.")

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


def _is_metal(material: str) -> bool:
    stem = material.split("_")[0]
    return stem in METAL_MATERIAL_NAMES


def currency_from_coin_standard(civ_id: str, coin_standard: Mapping, currency_name: str,
                                issuer: Optional[AgentId] = None) -> CurrencySpec:
    """Read a civilisation's `coin_standard` block. Fields used: `regime` (optional, one of REGIMES),
    `material`, `kg_per_unit`, `mint_charge_share` (optional). Without `regime` the regime is inferred from
    whether the material is a metal (a struck coin; a weighed metal needs `regime` stated)."""
    regime = coin_standard.get("regime")
    material = coin_standard.get("material")
    per_unit = float(coin_standard.get("kg_per_unit") or 0.0)
    if regime is not None and regime not in REGIMES:
        raise ValueError("%s: unknown money regime %r" % (civ_id, regime))
    if regime is None:
        if not material or per_unit <= 0.0:
            regime = "fiat"
        else:
            regime = "struck_coin" if _is_metal(material) else "commodity"
    if regime == "fiat":
        return CurrencySpec(currency_name, "fiat", None, 0.0, issuer)
    if not material or per_unit <= 0.0:
        raise ValueError("%s: %s money needs a material and kg_per_unit" % (civ_id, regime))
    return CurrencySpec(currency_name, regime, material, per_unit,
                        issuer if regime == "struck_coin" else None,
                        float(coin_standard.get("mint_charge_share", 0.0)))


def mint_parity(spec: CurrencySpec) -> float:
    """Price in money of one unit of the backing good at which a unit of money is worth its metal."""
    return 1.0 / spec.backing_per_unit


def mint_price(spec: CurrencySpec) -> float:
    """Money the mint pays per unit of bullion: parity less the mint charge."""
    return (1.0 - spec.mint_charge_share) / spec.backing_per_unit


def arbitrage(spec: CurrencySpec, bullion_price: float, holdings_of_backing: Mapping[AgentId, float],
              money_holdings: Mapping[AgentId, float],
              tile: types.TileId = "") -> Tuple[list, list]:
    """Holders bring bullion to the mint when it sells below what the mint pays, and melt money when
    bullion is worth more than the money. Weighed metal and commodity money work the same way with the mint
    standing for the exchange between balance and goods (no charge, no seigniorage). Fiat does nothing.
    `tile` is where the bullion is delivered or received."""
    if spec.regime == "fiat" or spec.backing_good is None or bullion_price <= 0.0:
        return [], []
    transfers, moves = [], []
    pay, parity = mint_price(spec), mint_parity(spec)
    if bullion_price < pay:
        share = min(1.0, ARBITRAGE_SPEED * (pay - bullion_price) / pay)
        for agent, metal in holdings_of_backing.items():
            brought = metal * share
            if brought <= 0.0 or types.is_edge(agent):
                continue
            moves.append(GoodsMove(agent, types.EDGE_MINT, spec.backing_good, tile, brought, "bullion to mint"))
            struck = brought / spec.backing_per_unit
            to_holder = struck * (1.0 - spec.mint_charge_share)
            transfers.append(Transfer(types.EDGE_MINT, agent, spec.currency_id, to_holder, "coin struck"))
            if spec.issuer is not None and struck - to_holder > 0.0:
                transfers.append(Transfer(types.EDGE_MINT, spec.issuer, spec.currency_id,
                                          struck - to_holder, "seigniorage"))
    elif bullion_price > parity:
        share = min(1.0, ARBITRAGE_SPEED * (bullion_price - parity) / bullion_price)
        for agent, coin in money_holdings.items():
            melted = coin * share
            if melted <= 0.0 or types.is_edge(agent):
                continue
            transfers.append(Transfer(agent, types.EDGE_MINT, spec.currency_id, melted, "coin melted"))
            moves.append(GoodsMove(types.EDGE_MINT, agent, spec.backing_good, tile,
                                   melted * spec.backing_per_unit, "bullion from melting"))
    return transfers, moves


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


def price_level(prices_now: Mapping[GoodId, float], prices_base: Mapping[GoodId, float],
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
