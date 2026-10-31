"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes. Nothing else survives a year.
"""
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
                       "last_dividends", "ways", "carried")


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
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> last year's quantity
    unsold: Dict[str, float] = field(default_factory=dict)               # market_key -> quantity sellers would have sold at the year's price and did not
    unmet: Dict[str, float] = field(default_factory=dict)                # market_key -> quantity buyers wanted at the year's price beyond what was sold
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
        """The record as plain data; money in `skip_currencies` (another owner's currency in the shared book) is left out."""
        return {
            "book": self.book.to_record(skip=skip_currencies),
            "memory": plain(self.memory),
            "currency": plain(self.currency),
            "cohorts": {key: plain(value) for key, value in sorted(self.cohorts.items())},
            "producers": {key: plain(value) for key, value in sorted(self.producers.items())},
            "merchants": {key: _merchant_record(value) for key, value in sorted(self.merchants.items())},
            "loans": self.contracts.to_records(facilities=False),
            "loan_requests": [plain(request) for request in self.loan_requests],
            "remembered_defaults": self.remembered_defaults,
            "credit_losses": self.credit_losses,
            "loss_rates": self.loss_rates,
            "losses_seen": self.losses_seen,
            "workforce": market_state_to_plain(self.workforce),
            "property_income": self.property_income,
            "volumes": self.volumes,
            "unsold": self.unsold,
            "unmet": self.unmet,
            "opening_basket": self.opening_basket,
            "opening_demand": self.opening_demand,
            "opening_own_grown": self.opening_own_grown,
            "opening_sold_hours_per_worker": self.opening_sold_hours_per_worker,
            "opening_sold_hours_by_area": self.opening_sold_hours_by_area,
            "opening_demand_by_country": self.opening_demand_by_country,
            "expansion_runs": self.expansion_runs,
            "index_base_prices": self.index_base_prices,
            "worn_runs": self.worn_runs,
            "state_budget": plain(self.state_budget),
            "land_rent": self.land_rent,
            "land_mean_value": self.land_mean_value,
            "titles": {tile: dict(held) for tile, held in sorted(self.titles.items())},
            "tenancies": {tile: [dict(row) for row in rows] for tile, rows in sorted(self.tenancies.items())},
            "cleared_hectares": dict(sorted(self.cleared_hectares.items())),
            "fugitives": {area: dict(row) for area, row in sorted(self.fugitives.items())},
            "bondage": {cohort: dict(bond) for cohort, bond in sorted(self.bondage.items())},
            "bonded_held": plain(self.bonded_held),
            "tax_history": {form: dict(row) for form, row in sorted(self.tax_history.items())},
            "margin_years": self.margin_years,
            "hours_hired": self.hours_hired,
            "hours_hired_by_others": self.hours_hired_by_others,
            "hours_idle": self.hours_idle,
            "sold_share_expected": self.sold_share_expected,
            "funds_offered": self.funds_offered,
            "lent_by_borrower": self.lent_by_borrower,
            "credit_granted": self.credit_granted,
            "banks": {key: plain(value) for key, value in sorted(self.banks.items())},
            "shares": {producer: dict(sorted(held.items())) for producer, held in sorted(self.shares.items())},
            "last_dividends": dict(sorted(self.last_dividends.items())),
            "capital": self.capital.to_plain(),
            "curves": self.curves,
            "ways": {key: dict(built) for key, built in sorted(self.ways.items())},
            "area_imbalance": self.area_imbalance,
            "carried": {key: dict(row) for key, row in sorted(self.carried.items())},
            "carried_goods": self.carried_goods,
            "spin_up_result": dict(self.spin_up_result),
        }

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "EconomyRecord":
        built = cls(
            book=Book.from_record(record["book"]),
            memory=MarketMemory(**record["memory"]),
            currency=CurrencySpec(**record["currency"]),
            cohorts={key: Cohort(**value) for key, value in record["cohorts"].items()},
            producers={key: Producer(**value) for key, value in record["producers"].items()},
            merchants={key: _merchant_from(value) for key, value in record["merchants"].items()},
            loan_requests=[LoanRequest(**request) for request in record["loan_requests"]],
            remembered_defaults=dict(record["remembered_defaults"]),
            credit_losses=dict(record["credit_losses"]),
            loss_rates=dict(record["loss_rates"]),
            losses_seen=dict(record["losses_seen"]),
            workforce=market_state_from_plain(record["workforce"]),
            property_income=dict(record["property_income"]),
            volumes=dict(record["volumes"]),
            unsold=dict(record["unsold"]),
            unmet=dict(record["unmet"]),
            opening_basket=dict(record["opening_basket"]),
            opening_demand=dict(record["opening_demand"]),
            opening_own_grown=dict(record["opening_own_grown"]),
            opening_sold_hours_per_worker=float(record["opening_sold_hours_per_worker"]),
            opening_sold_hours_by_area=dict(record["opening_sold_hours_by_area"]),
            opening_demand_by_country={country: dict(demand) for country, demand in record["opening_demand_by_country"].items()},
            expansion_runs=dict(record["expansion_runs"]),
            index_base_prices=dict(record["index_base_prices"]),
            worn_runs=dict(record["worn_runs"]),
            state_budget=StateBudget(**record["state_budget"]),
            land_rent=dict(record["land_rent"]),
            land_mean_value=dict(record["land_mean_value"]),
            titles={tile: dict(held) for tile, held in record["titles"].items()},
            tenancies={tile: [dict(row) for row in rows] for tile, rows in record["tenancies"].items()},
            cleared_hectares=dict(record["cleared_hectares"]),
            fugitives={area: dict(row) for area, row in record["fugitives"].items()},
            bondage={cohort: dict(bond) for cohort, bond in record["bondage"].items()},
            bonded_held=plain(record["bonded_held"]),
            tax_history={form: dict(row) for form, row in record["tax_history"].items()},
            margin_years=dict(record["margin_years"]),
            hours_hired=dict(record["hours_hired"]),
            hours_hired_by_others=dict(record["hours_hired_by_others"]),
            hours_idle=dict(record["hours_idle"]),
            sold_share_expected=dict(record["sold_share_expected"]),
            funds_offered=record["funds_offered"],
            lent_by_borrower=dict(record["lent_by_borrower"]),
            credit_granted=dict(record["credit_granted"]),
            banks={key: Bank(**value) for key, value in record["banks"].items()},
            shares={producer: dict(held) for producer, held in record["shares"].items()},
            last_dividends=dict(record["last_dividends"]),
            capital=CapitalState.from_plain(record["capital"]),
            curves=dict(record["curves"]),
            ways={key: dict(built) for key, built in record["ways"].items()},
            area_imbalance=record["area_imbalance"],
            carried={key: dict(row) for key, row in record["carried"].items()},
            carried_goods=record["carried_goods"],
            spin_up_result=dict(record["spin_up_result"]),
        )
        built.contracts.load_records(record["loans"])
        return built


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
