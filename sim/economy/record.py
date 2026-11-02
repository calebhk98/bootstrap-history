"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes. Nothing else survives a year.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from sim.contracts import Contracts
from sim.rekey import rekey
from sim.labour.api import MarketState, market_state_from_plain, market_state_to_plain

from .accounts import Book
from .banks import Bank
from .capital_state import CapitalState
from .households_cohort import Cohort
from .market_memory import KEY_SEPARATOR, MarketMemory
from .merchants import Merchant
from .merchants_transit import Shipment
from .producers import Producer
from .record_plain import plain
from .state_budget import StateBudget
from .types import AgentId, CurrencySpec, Loan, LoanRequest, TileId, TradeId


# the record's fields whose annotation names an AgentId (a test reads the source and holds this list to it)
AGENT_KEYED_FIELDS = ("cohorts", "producers", "merchants", "remembered_defaults", "credit_losses", "loss_rates", "losses_seen", "property_income",
                      "expansion_runs", "worn_runs", "titles", "bondage", "lent_by_borrower", "credit_granted", "banks", "shares",
                      "last_dividends", "capital", "bonded_held")

# the stores `to_record` writes sorted by key, and so a load reads back in that order
SAVED_SORTED_FIELDS = ("cohorts", "producers", "merchants", "titles", "tenancies", "bondage", "tax_history", "banks", "shares",
                       "last_dividends", "ways", "carried", "cleared_hectares", "fugitives")

# fields not saved: they hold only within-year state, empty between years
TRANSIENT_FIELDS = (
    "settling",    # true only inside the hidden spin-up, which finishes before any save
    "tax_farms",   # this year's farmer and price, set and cleared inside the year (its own comment says empty between years)
)

# the saved key where it differs from the field name
SAVED_KEYS = {"contracts": "loans"}


def _sorted_store(store: Dict[Any, Any]) -> Dict[Any, Any]:
    """The store in id order, and each inner dict too."""
    return {key: (dict(sorted(inner.items())) if isinstance(inner, dict) else inner) for key, inner in sorted(store.items())}


def _seat_sorted(store: Dict[Any, Any]) -> None:
    if list(store) != sorted(store):
        held = [(key, store[key]) for key in sorted(store)]
        store.clear()
        store.update(held)


@dataclass
class EconomyRecord:
    book: Book
    memory: MarketMemory
    currency: CurrencySpec
    cohorts: Dict[AgentId, Cohort] = field(default_factory=dict)
    producers: Dict[AgentId, Producer] = field(default_factory=dict)
    merchants: Dict[AgentId, Merchant] = field(default_factory=dict)
    contracts: Contracts = field(default_factory=Contracts)               # every debt: term loans here, facilities the purses'
    loan_requests: List[LoanRequest] = field(default_factory=list)       # made at last year's close
    remembered_defaults: Dict[AgentId, float] = field(default_factory=dict)   # losses a borrower caused, fading
    credit_losses: Dict[AgentId, float] = field(default_factory=dict)    # what each lender has lost to default
    loss_rates: Dict[AgentId, float] = field(default_factory=dict)       # each lender's expected loss per year of exposure, aging (loss_memory.py)
    losses_seen: Dict[AgentId, float] = field(default_factory=dict)      # credit_losses as of the last year's close
    workforce: MarketState = field(default_factory=MarketState)          # the labour core's state: people by labour area, trade and ability band
    property_income: Dict[AgentId, float] = field(default_factory=dict)  # dividends and interest last year
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> units delivered last year in all rounds; a market with no orders is absent
    unsold: Dict[str, float] = field(default_factory=dict)               # market_key -> units offered beyond what was delivered last year
    unmet: Dict[str, float] = field(default_factory=dict)                # market_key -> units buyers asked for at the asks they faced beyond what was delivered last year
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening, as far as the opening supplies it
    opening_demand: Dict[str, float] = field(default_factory=dict)       # good -> quantity households were seeded to want, supplied or not
    opening_own_grown: Dict[str, float] = field(default_factory=dict)    # good -> quantity households were seeded to grow on their own plots
    opening_sold_hours_per_worker: float = 0.0   # hours a working person was seeded to sell a year (zero: a whole working year)
    opening_sold_hours_by_area: Dict[str, float] = field(default_factory=dict)   # labour area -> hours a working person there was seeded to sell a year (empty: the one figure above)
    opening_demand_by_country: Dict[str, Dict[str, float]] = field(default_factory=dict)  # country -> good -> quantity its households were seeded to want
    expansion_runs: Dict[AgentId, float] = field(default_factory=dict)   # capacity a loan request would build
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    worn_runs: Dict[AgentId, float] = field(default_factory=dict)        # plant that wore out last year, to rebuild
    state_budget: StateBudget = field(default_factory=StateBudget)       # the state's revenue and this year's plan
    land_rent: Dict[TileId, float] = field(default_factory=dict)         # rent per hectare producers paid, by tile
    land_mean_value: Dict[TileId, float] = field(default_factory=dict)   # tile -> mean output value a hectare of the uses that set its rent (entrant_rent.py)
    land_ceded: Dict[TileId, float] = field(default_factory=dict)        # tile -> hectares let to producers that outbid the households' plots (land_priority.py)
    titles: Dict[TileId, Dict[AgentId, float]] = field(default_factory=dict)   # tile -> holder -> share of its land (titles.py)
    tenancies: Dict[TileId, List[Dict[str, Any]]] = field(default_factory=dict)   # tile -> rows of tenant, lessor, share, arrears
    cleared_hectares: Dict[TileId, float] = field(default_factory=dict)   # tile -> ground cleared and taken up, added to its cropland (titles_ground.py)
    bondage: Dict[AgentId, Dict[str, Any]] = field(default_factory=dict)   # household cohort -> creditor, debt left, years left (bondage.py)
    bonded_held: Dict[TileId, Dict[TradeId, Dict[AgentId, float]]] = field(default_factory=dict)   # tile -> trade -> employer -> bought bonded people it holds (bondage_hours.py)
    tax_history: Dict[str, Dict[str, float]] = field(default_factory=dict)   # form -> last year's base and the state's own take (tax_farming.py)
    tax_farms: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # form -> this year's farmer and price; empty between years
    margin_years: Dict[str, int] = field(default_factory=dict)           # market_key -> years in a row the expected price stood above the entry price
    hours_hired: Dict[str, float] = field(default_factory=dict)          # labour market_key -> hours hired last year
    hours_hired_by_others: Dict[str, float] = field(default_factory=dict)   # labour market_key -> hours hired last year by employers that are not producers (hours_hired_by_others.py)
    hours_idle: Dict[str, float] = field(default_factory=dict)           # labour market_key -> hours offered and not hired last year
    sold_share_expected: Dict[str, float] = field(default_factory=dict)  # labour market_key -> share of offered hours households expect to sell, smoothed over the years (household_work_year.py)
    funds_offered: float = 0.0                                           # savings on offer at the last lending, home currency
    lent_by_borrower: Dict[AgentId, float] = field(default_factory=dict)  # what each borrower was lent at the last lending
    credit_granted: Dict[AgentId, float] = field(default_factory=dict)   # what the last clearing granted each credit line asked for (credit_lines.py)
    banks: Dict[AgentId, Bank] = field(default_factory=dict)             # the banks households deposit with (banks.py)
    shares: Dict[AgentId, Dict[AgentId, float]] = field(default_factory=dict)   # producer -> holder -> part of its equity the holder bought (shares.py)
    last_dividends: Dict[AgentId, float] = field(default_factory=dict)   # producer -> the dividend it paid at its last close
    capital: CapitalState = field(default_factory=CapitalState)          # hazard records, insurers with their policies, and funds, keyed by AgentId (capital_state.py)
    curves: Dict[str, Any] = field(default_factory=dict)                 # market_key -> the book of the last clearing at the port (market_curves.py)
    ways: Dict[str, Dict[str, Any]] = field(default_factory=dict)        # the built ways the market areas are partitioned for
    area_imbalance: float = 1.0                                          # the return-trip emptiness the market areas were partitioned for (its memory is keyed by those areas)
    settling: bool = False                                               # in the hidden spin-up: households' spending rises as far as their wealth allows
    spin_up_result: Dict[str, Any] = field(default_factory=dict)         # how the hidden first stage ended: settled, years run, last gap (empty: no spin-up ran)
    carried: Dict[str, Dict[str, float]] = field(default_factory=dict)   # tonnes the merchants carried last year: origin tile -> destination tile (sim.geography.flow_ledger)
    carried_goods: Dict[str, Dict[str, Dict[str, List[float]]]] = field(default_factory=dict)   # the same flows by good: good -> origin -> destination -> [tonnes, value at origin's price, value at destination's price] (carried_book.py)
    fugitives: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # labour area people fled from -> people still away, arrears owed per head, the area they went to (flight_year.py)
    output_by_tile: Dict[TileId, Dict[str, float]] = field(default_factory=dict)   # tile -> good -> units the home producers made last year

    @property
    def loans(self) -> List[Loan]:
        """The term loans, in the order they were struck."""
        return self.contracts.term_loans

    @loans.setter
    def loans(self, loans: List[Loan]) -> None:
        self.contracts.term_loans = loans

    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """`old` becomes `new` in the book, the contracts and every store keyed by an agent id (the fields typed so),
        and as the borrower of a request; what each holds or owes is added to what `new` already has."""
        self.book.rename_agent(old, new)
        self.contracts.rename(old, new)
        for name in AGENT_KEYED_FIELDS:
            setattr(self, name, rekey(getattr(self, name), old, new))
        self.loan_requests = rekey(self.loan_requests, old, new)

    def sort_in_saved_order(self) -> None:
        """Re-seat the keyed stores the save writes in id order, in place, so a live game iterates them as a loaded one does."""
        for name in SAVED_SORTED_FIELDS:
            _seat_sorted(getattr(self, name))
            for inner in getattr(self, name).values():
                if isinstance(inner, dict):
                    _seat_sorted(inner)

    def to_record(self, skip_currencies=()) -> Dict[str, Any]:
        """The record as plain data, a field each (`dataclasses.fields`), the stores in SAVED_SORTED_FIELDS written in id
        order; money in `skip_currencies` (another owner's currency in the shared book) is left out."""
        saved: Dict[str, Any] = {}
        for each in dataclasses.fields(self):
            name = each.name
            value = getattr(self, name)
            if name in TRANSIENT_FIELDS:
                continue
            if name == "book":
                saved[name] = self.book.to_record(skip=skip_currencies)
            elif name in ENCODERS:
                saved[SAVED_KEYS.get(name, name)] = ENCODERS[name](value)
            else:
                saved[name] = plain(_sorted_store(value) if name in SAVED_SORTED_FIELDS else value)
        return saved

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "EconomyRecord":
        return cls(**{each.name: DECODERS[each.name](record[SAVED_KEYS.get(each.name, each.name)]) if each.name in DECODERS
                       else plain(record[each.name])
                       for each in dataclasses.fields(cls) if each.name not in TRANSIENT_FIELDS})


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


def _contracts_from(records: List[Dict[str, Any]]) -> Contracts:
    contracts = Contracts()
    contracts.load_records(records)
    return contracts


# the fields the generic copy cannot write or read: a dataclass or a class with its own record, or a key that is not a string
ENCODERS = {
    "merchants": lambda merchants: {key: _merchant_record(value) for key, value in sorted(merchants.items())},
    "contracts": lambda contracts: contracts.to_records(facilities=False),
    "workforce": market_state_to_plain,
    "capital": lambda capital: capital.to_plain(),
}
DECODERS = {
    "book": Book.from_record,
    "memory": lambda value: MarketMemory(**value),
    "currency": lambda value: CurrencySpec(**value),
    "cohorts": lambda value: {key: Cohort(**each) for key, each in value.items()},
    "producers": lambda value: {key: Producer(**each) for key, each in value.items()},
    "merchants": lambda value: {key: _merchant_from(each) for key, each in value.items()},
    "contracts": _contracts_from,
    "loan_requests": lambda value: [LoanRequest(**each) for each in value],
    "workforce": market_state_from_plain,
    "state_budget": lambda value: StateBudget(**value),
    "banks": lambda value: {key: Bank(**each) for key, each in value.items()},
    "capital": CapitalState.from_plain,
}
