"""What an actor keeps, by kind: coin, goods, land, loans and shares, as theft, sack and banditry see it.

An actor lists only what it holds. A firm keeps no stock of goods and no land of its own, so it exposes coin,
loans and shares; a state exposes its stores; the founder exposes his purse, granary and material stock, farm and
forest land. Funds lenders have out on loan are a claim, not coin in a strongroom, so the lent share of a purse
counts as loans and the rest as coin.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple

from sim.agents.api import joint_stock
from sim.labour.api import wage_provider
from sim.world import capital_market


@dataclass
class GoodsLot:
    """Tonnes of one good an actor holds, what a tonne fetches, and how to remove tonnes from the holder's stock."""
    name: str
    tonnes: float
    price_per_tonne: float
    take: Callable[[float], None]


@dataclass
class Exposure:
    """Value held by kind (a kind the actor does not hold is absent), the lots of goods behind the goods value,
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


class HoldingsExposureMixin:
    """Mixed into `Sim`."""

    def lent_share(self):
        """Share of lenders' funds out on loan at the last meeting of the market (as `state_lending` reads it)."""
        record = self._market_record()
        if record is None or record.supply <= 0.0:
            return 0.0
        demanded = capital_market.utilisation(record.background + sum(record.loans.values()), record.supply)
        return min(1.0 - capital_market.LENDER_RESERVE_SHARE, demanded)

    def actor_exposure(self, actor, price_of_tonne, find_actor):
        """What a firm or a state keeps: its purse, the stores it holds, and the shares it owns in others."""
        exposure = Exposure()
        _add_purse(exposure, actor.money, self.lent_share())
        stores = actor.record.stores
        for material in sorted(stores):
            def take(tonnes, material=material):
                stores[material] = max(0.0, stores[material] - tonnes)
            _add_lot(exposure, GoodsLot(material, stores[material], price_of_tonne(material), take))
        worth = joint_stock.shares_worth(actor.record.holdings, find_actor)
        if worth > 0.0:
            exposure.values["shares"] = worth
        return exposure

    def founder_exposure(self):
        """What the founder keeps: purse, material stock and granary, farm and forest land."""
        exposure = Exposure()
        household = self.state.household
        _add_purse(exposure, household.capital, self.lent_share())
        stock = self._material_stock()
        for key in sorted(stock):
            quote = self.goods_market.quote(key)
            if quote:
                def take(tonnes, key=key):
                    stock[key] = max(0.0, stock[key] - tonnes)
                _add_lot(exposure, GoodsLot(key, stock[key], quote["sell_per_tonne"], take))
        staple_name = wage_provider.staple_material(self.civ)
        staple = self.goods_market.quote(staple_name)
        if staple:
            def take_grain(tonnes):
                self.farm_stock_kg = max(0.0, self.farm_stock_kg - tonnes * 1000.0)
            _add_lot(exposure, GoodsLot(staple_name, self.farm_stock_kg / 1000.0, staple["sell_per_tonne"], take_grain))
        land = ((self.farm_hectares or 0.0) * self.farm_price_per_hectare()
                + (self.forest_ha or 0.0) * self.FOREST_COST_PER_HA * self.price_index)
        if land > 0.0:
            exposure.values["land"] = land
        return exposure
