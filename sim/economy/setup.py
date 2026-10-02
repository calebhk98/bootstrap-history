"""What one civilisation's economy is built from: the facts that do not change from year to year.

The port (sim/engine/economy_port.py) or a tool fills an `EconomySetup` from data and the engine's
opening state; nothing in it is a model outcome except the opening prices and wages, which only seed
the first year's expectations and are forgotten as soon as markets clear.
"""
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from sim.world import demand

from .tile_costs import Edge
from .types import AgentId, CurrencySpec, GoodId, GoodSpec, Recipe, TileId, TileSpec, TradeId

LABOUR_AREA_PREFIX = "work@"


def labour_area(tile: TileId) -> str:
    """People hire and are hired on their own tile: a tile is the labour market's area."""
    return LABOUR_AREA_PREFIX + tile


@dataclass(frozen=True)
class TradeSpec:
    trade_id: TradeId
    training_years: float = 0.0
    fatality_risk_per_year: float = 0.0


@dataclass
class EconomySetup:
    civ_id: str
    currency: CurrencySpec
    state_agent: AgentId
    tiles: Dict[TileId, TileSpec]
    edges: Tuple[Edge, ...]
    carriage_rates: Dict[str, float]               # money per tonne-km by mode, at the opening
    handling_rates: Dict[str, float]               # money per tonne per leg by mode, at the opening
    specs: Dict[GoodId, GoodSpec]
    recipes: Dict[str, Recipe]
    basket: Any                                    # households.Basket
    trades: Dict[TradeId, TradeSpec]
    tax_forms: Tuple[Any, ...]                     # taxes.TaxForm
    state_capacity: float
    working_hours_per_year: float
    working_share: float
    gini: float
    opening_population_by_tile: Dict[TileId, float]
    opening_prices: Dict[GoodId, float]            # money per unit, seeds expectations only
    opening_wages: Dict[TradeId, float]            # money per hour, seeds expectations only
    opening_rate: float
    capital_tile: TileId
    port_tile: TileId
    unskilled_trade: TradeId = "labourer"
    yield_factor_by_recipe_tile: Dict[str, float] = field(default_factory=dict)

    @property
    def currency_id(self) -> str:
        return self.currency.currency_id


def recipe_tile_key(recipe_id: str, tile: TileId) -> str:
    return recipe_id + "@" + tile


def goods_specs(goods: Mapping[GoodId, str], spoilage_rates: Mapping[GoodId, Mapping[str, Any]],
                service_lives: Optional[Mapping[GoodId, float]] = None) -> Dict[GoodId, GoodSpec]:
    """A `GoodSpec` per good from its unit (mass where the unit says), the spoilage table and any
    stated service life. `goods` maps each good to a category label from data."""
    service_lives = service_lives or {}
    specs = {}
    for good, category in sorted(goods.items()):
        mass = demand.mass_in_kg_or_none(good, 1.0)
        decay_rate = float((spoilage_rates.get(good) or {}).get("rate", 0.0))   # continuous, per year
        specs[good] = GoodSpec(good_id=good, unit_mass_kg=mass if mass is not None else 1.0,
                               spoilage_per_year=1.0 - math.exp(-decay_rate),
                               service_life_years=float(service_lives.get(good, 0.0)),
                               category=category)
    return specs
