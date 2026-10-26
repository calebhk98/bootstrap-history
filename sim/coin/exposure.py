"""What an actor keeps, by kind: coin, goods, land, loans and shares, as theft, sack and banditry see it.

An actor lists only what it holds. A firm keeps no stock of goods and no land of its own, so it exposes coin,
loans and shares; a state exposes its stores; a household exposes its purse, granary and material stock, farm and
forest land. Funds lenders have out on loan are a claim, not coin in a strongroom, so the lent share of a purse
counts as loans and the rest as coin. A lot names where its goods are kept (`store`); taking them is the ledger's
command, so an exposure holds amounts only.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from sim.ledger.api import STORE_ACTOR, STORE_GRANARY, STORE_STOCK


@dataclass
class GoodsLot:
    """Tonnes of one good a holder keeps, what a tonne fetches, and the store the tonnes are taken from."""
    name: str
    tonnes: float
    price_per_tonne: float
    store: str
    actor: Optional[str] = None


@dataclass
class Exposure:
    """Value held by kind (a kind the holder does not hold is absent), the lots of goods behind the goods value,
    and the positive purse that pays for what is lost as a claim."""
    values: Dict[str, float] = field(default_factory=dict)
    lots: List[GoodsLot] = field(default_factory=list)
    purse: float = 0.0


def split_purse(money: float, lent_share: float) -> Tuple[float, float]:
    """(coin kept, funds lent out) of a purse; nothing of a purse in debt."""
    held = max(0.0, money)
    lent = held * min(1.0, max(0.0, lent_share))
    return held - lent, lent


def _add_purse(exposure: Exposure, money: float, lent_share: float) -> None:
    coin, lent = split_purse(money, lent_share)
    exposure.purse = max(0.0, money)
    if coin > 0.0:
        exposure.values["coin"] = coin
    if lent > 0.0:
        exposure.values["loans"] = lent


def _add_lot(exposure: Exposure, lot: GoodsLot) -> None:
    if lot.tonnes > 0.0 and lot.price_per_tonne > 0.0:
        exposure.lots.append(lot)
        exposure.values["goods"] = exposure.values.get("goods", 0.0) + lot.tonnes * lot.price_per_tonne


def actor_exposure(actor_id: str, money: float, stores: Mapping[str, float], price_of_tonne: Callable[[str], float],
                   shares_worth: Callable[[], float], lent_share: float) -> Exposure:
    """What a firm or a state keeps: its purse, the stores it holds, and the shares it owns in others."""
    exposure = Exposure()
    _add_purse(exposure, money, lent_share)
    for material in sorted(stores):
        _add_lot(exposure, GoodsLot(material, stores[material], price_of_tonne(material), STORE_ACTOR, actor_id))
    worth = shares_worth()
    if worth > 0.0:
        exposure.values["shares"] = worth
    return exposure


def household_exposure(purse: float, lent_share: float, stock: Mapping[str, float], quotes: Mapping[str, Optional[Mapping]],
                       staple_name: str, staple_quote: Optional[Mapping], granary_kg: float, land_value: float) -> Exposure:
    """What a household keeps: purse, material stock and granary, farm and forest land. `quotes` holds the market's
    quote of each commodity in the stock (None for one the market does not price); `land_value` is the worth of the
    farm and forest, 0 when it has none."""
    exposure = Exposure()
    _add_purse(exposure, purse, lent_share)
    for key in sorted(stock):
        quote = quotes[key]
        if quote:
            _add_lot(exposure, GoodsLot(key, stock[key], quote["sell_per_tonne"], STORE_STOCK))
    if staple_quote:
        _add_lot(exposure, GoodsLot(staple_name, granary_kg / 1000.0, staple_quote["sell_per_tonne"], STORE_GRANARY))
    if land_value > 0.0:
        exposure.values["land"] = land_value
    return exposure


def land_value(farm_hectares: Optional[float], price_per_hectare: Optional[float], forest_hectares: Optional[float],
               forest_cost_per_hectare: float, price_index: float) -> float:
    """Farm land at its price a hectare plus forest at its cost a hectare scaled by the price index; a household with
    no farm yet has no price per hectare and no farm."""
    return (farm_hectares or 0.0) * price_per_hectare + (forest_hectares or 0.0) * forest_cost_per_hectare * price_index
