"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes; and eight owned sub-records hold one domain each: credit, capital markets, land, goods,
labour, carriage, tax and unfree labour (`credit_record.py`, `capital_markets_record.py`, `land_record.py`, `goods_record.py`,
`labour_record.py`, `carriage_record.py`, `tax_record.py`, `unfree_record.py`). Nothing else survives a year.

`book` is the shared ledger and has no owner module: any module moves money and goods, but only through `Book`'s own
methods (`transfer`, `transfer_many`, `move_many`, ...), never by writing its tables. `tools/done_check.sh` counts the
calls to them outside the files that define them, and `tools/check_record_owners.py` flags a direct write to `book`.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Tuple

from .accounts import Book
from .capital_markets_record import CapitalMarketsRecord
from .carriage_record import CarriageRecord
from .credit_record import CreditRecord
from .goods_record import GoodsRecord
from .labour_record import LabourRecord
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
from .types import AgentId, CurrencySpec
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
    labour: LabourRecord = field(default_factory=LabourRecord)                      # labour_record.py
    goods: GoodsRecord = field(default_factory=GoodsRecord)                         # goods_record.py
    state_budget: StateBudget = field(default_factory=StateBudget)       # the state's revenue and this year's plan
    settling: bool = False                                               # in the hidden spin-up: households' spending rises as far as their wealth allows
    spin_up_result: Dict[str, Any] = field(default_factory=dict)         # how the hidden first stage ended: settled, years run, last gap (empty: no spin-up ran)

    AGENT_KEYED = ("cohorts", "producers", "merchants")
    SAVED_SORTED = ("cohorts", "producers", "merchants")
    TABLE_OWNERS: ClassVar[Dict[str, Tuple[str, ...]]] = {
        "cohorts": ("households_cohort",), "producers": ("producer_table",), "merchants": ("merchants", "merchants_dispatch")}   # modules that write each agent table
    TRANSIENT = ("settling",)   # true only inside the hidden spin-up, which finishes before any save
    ENCODERS = {
        "merchants": lambda merchants: {key: _merchant_record(value) for key, value in sorted(merchants.items())},
    }
    DECODERS = {
        "book": Book.from_record,
        "memory": lambda value: MarketMemory(**value),
        "currency": lambda value: CurrencySpec(**value),
        "cohorts": lambda value: {key: Cohort(**each) for key, each in value.items()},
        "producers": lambda value: {key: Producer(**each) for key, each in value.items()},
        "merchants": lambda value: {key: _merchant_from(each) for key, each in value.items()},
        "state_budget": lambda value: StateBudget(**value),
    }

    @classmethod
    def owners_by_part(cls) -> Dict[str, Tuple[str, ...]]:
        """{part name: the sim/economy modules allowed to write it}, for every owned part, the memory, the budget and the agent tables
        (tools/check_record_owners.py)."""
        owners = dict(cls.TABLE_OWNERS)
        for each in dataclasses.fields(cls):
            if hasattr(each.type, "OWNERS"):
                owners[each.name] = each.type.OWNERS
        return owners

    @classmethod
    def part_class_names(cls) -> Dict[str, str]:
        """{class name: part name} for the classes whose instances are a whole part or a row of an agent table."""
        names = {}
        for each in dataclasses.fields(cls):
            if hasattr(each.type, "OWNERS"):
                names[each.type.__name__] = each.name
            elif each.name in cls.TABLE_OWNERS:
                names[each.type.__args__[1].__name__] = each.name
        return names

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
