"""What one civilisation's economy is built from: the facts that do not change from year to year.

The port (sim/engine/economy_port.py) or a tool fills an `EconomySetup` from data and the engine's
opening state; nothing in it is a model outcome except the opening prices and wages, which only seed
the first year's expectations and are forgotten as soon as markets clear.
"""
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from sim.world import demand

from .good_mass import unit_mass_and_source
from .market_areas import AreaMap
from .state_policy import StatePolicy
from .tile_costs import CarriageTable, carriage_table
from .types import AgentId, CurrencySpec, GoodId, GoodSpec, Recipe, SiteLimit, TileId, TileSpec, TradeId

LABOUR_AREA_PREFIX = "work@"


def labour_area(tile: TileId) -> str:
    """People hire and are hired on their own tile: a tile is the labour market's area."""
    return LABOUR_AREA_PREFIX + tile


def area_tile(area: str) -> TileId:
    """The tile a labour area stands for (the inverse of `labour_area`)."""
    return area[len(LABOUR_AREA_PREFIX):] if area.startswith(LABOUR_AREA_PREFIX) else area


@dataclass(frozen=True)
class TradeSpec:
    trade_id: TradeId
    training_years: float = 0.0
    fatality_risk_per_year: float = 0.0
    family: str = ""                  # trades that share skill: retraining within one is quicker


@dataclass
class EconomySetup:
    civ_id: str
    currency: CurrencySpec
    state_agent: AgentId
    tiles: Dict[TileId, TileSpec]
    carriage_rates: Dict[str, float]               # money per tonne-km by geography mode id, at the opening, carriers returning empty
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
    hiding: Any = None  # (rate, reach) -> share of its base a payer hides; the port hands in the actor layer's rule, None: none
    flight: Any = None  # the actors' flight rules (expected_penalty_of_leaving, arrears_owed_by_fugitive, share_after_immunity), handed in by the port; None: no flight
    debt_bondage_years: float = 0.0               # term of service a landless household in default owes its creditor; 0: the society has no debt bondage (bondage.py)
    import_duty_share: Dict[GoodId, float] = field(default_factory=dict)   # per good, the share of its landed price that is the state's tariff; the port sets it as the year's imports are offered
    carriage_rates_balanced: Dict[str, float] = field(default_factory=dict)   # likewise with the opposite flow filling every return; none: same
    carriage_crew: Dict[str, Tuple[str, float]] = field(default_factory=dict)   # mode id (land, river, sea) -> (crew trade, crew hours per tonne-km), geography's; none: carriage hires no hours
    carriage_handling: Dict[str, float] = field(default_factory=dict)   # mode id -> hours of handling a tonne each time a haul changes to the mode, for the modes whose handling the rates price
    carriage_handling_trade: Dict[str, str] = field(default_factory=dict)   # mode id -> the trade that works those handling hours (geography's `handling_trade`); a mode with none is handled by the unskilled trade
    carriage_carriers: Dict[str, Tuple[float, Tuple[Tuple[str, float], ...]]] = field(default_factory=dict)   # mode id -> (tonne-km a team moves a day, ((carrier good, units worn per tonne-km),)): what a tonne-km wears (carriage_wear); none: carriage wears nothing
    need_share_by_trade: Dict[str, float] = field(default_factory=dict)   # trade -> its share of the society's non-farm labour need (recipes and carriage), seeds the trades no producer's runs staff
    carriage_wage: float = 0.0     # the wage an hour (unskilled trade) the land carriage rates were priced at; 0: they follow no wage
    fuel_need: str = "warmth"           # the basket need fuel meets; a hearth's cooking fuel is added to its floor
    hunger_need: str = "food"           # the basket need whose unmet floor counts as hunger
    yield_factor_by_recipe_tile: Dict[str, float] = field(default_factory=dict)
    land_per_run: Dict[str, float] = field(default_factory=dict)      # hectare-years of land a run takes
    basket_by_tile: Dict[TileId, Any] = field(default_factory=dict)   # floors that follow the tile's climate
    household_work: Dict[str, Any] = field(default_factory=dict)      # hours of household work by task (data/world/household_work.json); empty: none is modelled
    ready_to_eat: frozenset = frozenset()                             # goods a household with no hearth can eat as bought
    milled_as: Dict[str, str] = field(default_factory=dict)           # per grain, the good it is milled into (needs.json); a household weighs grinding it against buying that
    servant_trade: str = "domestic_servant"                           # the trade whose wage is the price of an hour of household work
    state_policy: StatePolicy = field(default_factory=StatePolicy)   # how the state budgets and finances a deficit
    site_limits: Tuple[SiteLimit, ...] = ()     # where site-bound recipes can run, and how much (sites.py)
    mint_recipe: Optional[Recipe] = None   # how the mint strikes coin: the production entry the coin standard names
    held_nodes: Tuple[str, ...] = ()    # tech nodes the society holds; geography's sea lanes may need them
    world_map: Any = None               # geography's map the tiles lie on (the base map when None)
    coin_per_unit: float = 1.0          # the economy counts money in this many coins (the port converts)
    improvements: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # built roads and track by edge key
    opening_store_output: Dict[GoodId, Tuple[Tuple[float, float, float], ...]] = field(default_factory=dict)
    # per durable good, its past workings (kg a year, years worked, years since the last output) from the deposits
    opening_store_gaps: Dict[GoodId, str] = field(default_factory=dict)   # why a good has no workings, for audit
    # country -> the recipes its producers can run (what its society's techniques allow); empty: every recipe anywhere
    recipes_by_country: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    kernels: Dict[str, Any] = field(default_factory=dict)   # the markets module's bound kernels by name (markets/kernels.py); absent: the references
    # tile -> {owner, control} (geography's tile_owners), shared with the game's state; empty: the tiles' own countries
    tile_owners: Dict[TileId, Dict[str, str]] = field(default_factory=dict)

    def carriage_rates_at(self, imbalance: float = 1.0) -> Dict[str, float]:
        """Money per tonne-km by mode when `imbalance` of the carriers' return trips find no opposite flow
        (1: all return empty, the opening rates; 0: all return full). A carrier's cost is linear in the
        empty share of its return, so the rate lies on the line between the two."""
        if not self.carriage_rates_balanced:
            return dict(self.carriage_rates)
        share = max(0.0, min(1.0, imbalance))
        return {mode: self.carriage_rates_balanced.get(mode, rate)
                + share * (rate - self.carriage_rates_balanced.get(mode, rate))
                for mode, rate in self.carriage_rates.items()}

    def carriage_table(self, improvements=None, imbalance: float = 1.0) -> CarriageTable:
        """What it costs to move a tonne between this setup's tiles, over geography's route graph, with the
        built ways (this setup's own when none are given) and the return trips `imbalance` leaves empty."""
        ways = self.improvements if improvements is None else improvements
        return carriage_table(self.tiles, self.carriage_rates_at(imbalance), self.handling_rates, self.held_nodes,
                              self.world_map, ways, self.kernels.get("markets.least_cost_tree"))

    def area_map(self, carriage: Optional[CarriageTable] = None) -> AreaMap:
        """Market areas over this setup's tiles at its opening prices and people, partitioned by `carriage`
        (this setup's own carriage table when none is given)."""
        carriage = self.carriage_table() if carriage is None else carriage
        carriage.warm(remember=True)
        return AreaMap(self.tiles, carriage, [(self.specs[good], price) for good, price in
                                              sorted(self.opening_prices.items())
                                              if good in self.specs and price > 0.0],
                       self.opening_population_by_tile)

    def country_of(self, tile: TileId) -> str:
        """The civilisation whose people live on a tile: its owner when the owner map names one, else the
        setup's own unless the tile names another."""
        owned = self.tile_owners.get(tile)
        if owned:
            return owned["owner"]
        spec = self.tiles.get(tile)
        return (spec.country if spec is not None and spec.country else self.civ_id)

    def countries(self) -> Tuple[str, ...]:
        """Every civilisation with tiles in this economy, the home one first."""
        others = sorted({self.country_of(tile) for tile in self.tiles} - {self.civ_id})
        return (self.civ_id,) + tuple(others)

    def tiles_of(self, country: str) -> Tuple[TileId, ...]:
        return tuple(sorted(tile for tile in self.tiles if self.country_of(tile) == country))

    def recipe_allowed(self, recipe_id: str, tile: TileId) -> bool:
        """Whether the people on `tile` can run the recipe: their country's techniques allow it."""
        if not self.recipes_by_country:
            return True
        return recipe_id in self.recipes_by_country.get(self.country_of(tile), ())

    def basket_for(self, tile: TileId):
        """The needs of people living on a tile: the common basket with that tile's floors."""
        return self.basket_by_tile.get(tile, self.basket)

    @property
    def currency_id(self) -> str:
        return self.currency.currency_id


def recipe_tile_key(recipe_id: str, tile: TileId) -> str:
    return recipe_id + "@" + tile


def goods_specs(goods: Mapping[GoodId, str], spoilage_rates: Mapping[GoodId, Mapping[str, Any]],
                service_lives: Optional[Mapping[GoodId, float]] = None) -> Dict[GoodId, GoodSpec]:
    """A `GoodSpec` per good (its unit mass from `good_mass`), the spoilage table and any stated
    service life. `goods` maps each good to a category label from data."""
    service_lives = service_lives or {}
    production = demand.production_data()
    specs = {}
    for good, category in sorted(goods.items()):
        mass, _source = unit_mass_and_source(good, production)
        decay_rate = float((spoilage_rates.get(good) or {}).get("rate", 0.0))   # continuous, per year
        specs[good] = GoodSpec(good_id=good, unit_mass_kg=mass,
                               spoilage_per_year=1.0 - math.exp(-decay_rate),
                               service_life_years=float(service_lives.get(good, 0.0)),
                               category=category,
                               capital_asset=bool(production.get(good, {}).get("capital_asset", False)))
    return specs
