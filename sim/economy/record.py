"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes. Nothing else survives a year.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from sim.labour.api import MarketState, market_state_from_plain, market_state_to_plain

from .accounts import Book
from .capital_markets_record import CapitalMarketsRecord
from .carriage_record import CarriageRecord
from .credit_record import CreditRecord
from .land_record import LandRecord
from .households_cohort import Cohort
from .market_memory import KEY_SEPARATOR, MarketMemory
from .merchants import Merchant
from .merchants_transit import Shipment
from .producers import Producer
from .record_parts import OwnedRecord
from .record_plain import plain
from .state_budget import StateBudget
from .tax_record import TaxRecord
from .types import AgentId, CurrencySpec, TileId, TradeId
from .unfree_record import UnfreeRecord


@dataclass
class EconomyRecord(OwnedRecord):
    """The shared ledger (book, memory, currency), the agent tables, and one owned part per domain."""
    book: Book
    memory: MarketMemory
    currency: CurrencySpec
    cohorts: Dict[AgentId, Cohort] = field(default_factory=dict)
    producers: Dict[AgentId, Producer] = field(default_factory=dict)
    merchants: Dict[AgentId, Merchant] = field(default_factory=dict)
    credit: CreditRecord = field(default_factory=CreditRecord)                      # credit_record.py
    capital_markets: CapitalMarketsRecord = field(default_factory=CapitalMarketsRecord)   # capital_markets_record.py
    land: LandRecord = field(default_factory=LandRecord)                            # land_record.py
    unfree: UnfreeRecord = field(default_factory=UnfreeRecord)                      # unfree_record.py
    taxes: TaxRecord = field(default_factory=TaxRecord)                             # tax_record.py
    carriage: CarriageRecord = field(default_factory=CarriageRecord)                # carriage_record.py
    workforce: MarketState = field(default_factory=MarketState)          # the labour core's state: people by labour area, trade and ability band
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> units delivered last year in all rounds; a market with no orders is absent
    unsold: Dict[str, float] = field(default_factory=dict)               # market_key -> units offered beyond what was delivered last year
    unmet: Dict[str, float] = field(default_factory=dict)                # market_key -> units buyers asked for at the asks they faced beyond what was delivered last year
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening, as far as the opening supplies it
    opening_demand: Dict[str, float] = field(default_factory=dict)       # good -> quantity households were seeded to want, supplied or not
    opening_own_grown: Dict[str, float] = field(default_factory=dict)    # good -> quantity households were seeded to grow on their own plots
    opening_sold_hours_per_worker: float = 0.0   # hours a working person was seeded to sell a year (zero: a whole working year)
    opening_sold_hours_by_area: Dict[str, float] = field(default_factory=dict)   # labour area -> hours a working person there was seeded to sell a year (empty: the one figure above)
    opening_demand_by_country: Dict[str, Dict[str, float]] = field(default_factory=dict)  # country -> good -> quantity its households were seeded to want
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    state_budget: StateBudget = field(default_factory=StateBudget)       # the state's revenue and this year's plan
    margin_years: Dict[str, int] = field(default_factory=dict)           # market_key -> years in a row the expected price stood above the entry price
    hours_hired: Dict[str, float] = field(default_factory=dict)          # labour market_key -> hours hired last year
    hours_hired_by_employer: Dict[AgentId, Dict[TradeId, float]] = field(default_factory=dict)   # employer -> trade -> hours the last clearing hired for it
    hours_idle: Dict[str, float] = field(default_factory=dict)           # labour market_key -> hours offered and not hired last year
    sold_share_expected: Dict[str, float] = field(default_factory=dict)  # labour market_key -> share of offered hours households expect to sell, smoothed over the years (household_work_year.py)
    curves: Dict[str, Any] = field(default_factory=dict)                 # market_key -> the book of the last clearing at the port (market_curves.py)
    settling: bool = False                                               # in the hidden spin-up: households' spending rises as far as their wealth allows
    spin_up_result: Dict[str, Any] = field(default_factory=dict)         # how the hidden first stage ended: settled, years run, last gap (empty: no spin-up ran)
    output_by_tile: Dict[TileId, Dict[str, float]] = field(default_factory=dict)   # tile -> good -> units the home producers made last year

    AGENT_KEYED = ("cohorts", "producers", "merchants", "hours_hired_by_employer")
    SAVED_SORTED = ("cohorts", "producers", "merchants")
    TRANSIENT = ("settling",)   # true only inside the hidden spin-up, which finishes before any save
    ENCODERS = {
        "merchants": lambda merchants: {key: _merchant_record(value) for key, value in sorted(merchants.items())},
        "workforce": market_state_to_plain,
    }
    DECODERS = {
        "book": Book.from_record,
        "memory": lambda value: MarketMemory(**value),
        "currency": lambda value: CurrencySpec(**value),
        "cohorts": lambda value: {key: Cohort(**each) for key, each in value.items()},
        "producers": lambda value: {key: Producer(**each) for key, each in value.items()},
        "merchants": lambda value: {key: _merchant_from(each) for key, each in value.items()},
        "workforce": market_state_from_plain,
        "state_budget": lambda value: StateBudget(**value),
    }

    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """`old` becomes `new` in the book and in every store of the record and its parts keyed by an agent id; what each
        holds or owes is added to what `new` already has."""
        self.book.rename_agent(old, new)
        super().rename_agent(old, new)

    def to_record(self, skip_currencies=()) -> Dict[str, Any]:
        """The record as plain data; money in `skip_currencies` (another owner's currency in the shared book) is left out."""
        return self.saved_fields({"book": lambda book: book.to_record(skip=skip_currencies)})

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "EconomyRecord":
        return cls.from_saved_fields(record)


def _pair_keys(mapping: Dict[Tuple[str, str], Any]) -> Dict[str, Any]:
    return {first + KEY_SEPARATOR + second: value for (first, second), value in sorted(mapping.items())}


def _split_keys(mapping: Dict[str, Any]) -> Dict[Tuple[str, str], Any]:
    splitter = str.split
    return {tuple(splitter(key, KEY_SEPARATOR, 1)): value for key, value in mapping.items()}


def _merchant_record(merchant: Merchant) -> Dict[str, Any]:
    return {"agent_id": merchant.agent_id, "home_tile": merchant.home_tile, "owner": merchant.owner,
            "capital_base": merchant.capital_base,
            "expected_prices": _pair_keys(merchant.expected_prices),
            "expected_volumes": _pair_keys(merchant.expected_volumes),
            "routes": {key: [list(leg) for leg in legs] for key, legs in _pair_keys(merchant.routes).items()},
            "carriage_hours_wanted": merchant.carriage_hours_wanted,
            "carriage_money_wanted": merchant.carriage_money_wanted,
            "carrier_wear": merchant.carrier_wear, "carrier_team_days": merchant.carrier_team_days,
            "carrier_fleet_wanted": merchant.carrier_fleet_wanted,
            "in_transit": [plain(each) for each in merchant.in_transit],
            "price_history": _pair_keys(merchant.price_history)}


def _merchant_from(record: Dict[str, Any]) -> Merchant:
    return Merchant(agent_id=record["agent_id"], home_tile=record["home_tile"], owner=record["owner"],
                    capital_base=record["capital_base"],
                    expected_prices=_split_keys(record["expected_prices"]),
                    expected_volumes=_split_keys(record["expected_volumes"]),
                    routes={key: tuple(tuple(leg) for leg in legs) for key, legs in _split_keys(record["routes"]).items()},
                    carriage_hours_wanted=record["carriage_hours_wanted"],
                    carriage_money_wanted=record["carriage_money_wanted"],
                    carrier_wear=record["carrier_wear"], carrier_team_days=record["carrier_team_days"],
                    carrier_fleet_wanted=record["carrier_fleet_wanted"],
                    in_transit=[Shipment(**each) for each in record["in_transit"]],
                    price_history=_split_keys(record["price_history"]))
