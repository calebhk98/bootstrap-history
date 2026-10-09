"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes. Nothing else survives a year.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from sim.labour.api import MarketState, market_state_from_plain, market_state_to_plain

from .accounts import Book
from .households_cohort import Cohort
from .market_memory import KEY_SEPARATOR, MarketMemory
from .merchants import Merchant
from .producers import Producer
from .record_plain import plain
from .state_budget import StateBudget
from .types import AgentId, CurrencySpec, Loan, LoanRequest, TileId, TradeId


@dataclass
class EconomyRecord:
    book: Book
    memory: MarketMemory
    currency: CurrencySpec
    cohorts: Dict[AgentId, Cohort] = field(default_factory=dict)
    producers: Dict[AgentId, Producer] = field(default_factory=dict)
    merchants: Dict[AgentId, Merchant] = field(default_factory=dict)
    loans: List[Loan] = field(default_factory=list)
    loan_requests: List[LoanRequest] = field(default_factory=list)       # made at last year's close
    remembered_defaults: Dict[AgentId, float] = field(default_factory=dict)   # losses a borrower caused, fading
    credit_losses: Dict[AgentId, float] = field(default_factory=dict)    # what each lender has lost to default
    workforce: MarketState = field(default_factory=MarketState)          # the labour core's state: people by labour area, trade and ability band
    property_income: Dict[AgentId, float] = field(default_factory=dict)  # dividends and interest last year
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> last year's quantity
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening
    expansion_runs: Dict[AgentId, float] = field(default_factory=dict)   # capacity a loan request would build
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    worn_runs: Dict[AgentId, float] = field(default_factory=dict)        # plant that wore out last year, to rebuild
    state_budget: StateBudget = field(default_factory=StateBudget)       # the state's revenue and this year's plan
    land_rent: Dict[TileId, float] = field(default_factory=dict)         # rent per hectare producers paid, by tile
    margin_years: Dict[str, int] = field(default_factory=dict)           # market_key -> years in a row the expected price stood above the entry price
    hours_hired: Dict[str, float] = field(default_factory=dict)          # labour market_key -> hours hired last year
    funds_offered: float = 0.0                                           # savings on offer at the last lending, home currency
    lent_by_borrower: Dict[AgentId, float] = field(default_factory=dict)  # what each borrower was lent at the last lending
    curves: Dict[str, Any] = field(default_factory=dict)                 # market_key -> the book of the last clearing at the port (market_curves.py)
    ways: Dict[str, Dict[str, Any]] = field(default_factory=dict)        # the built ways the market areas are partitioned for

    def to_record(self, skip_currencies=()) -> Dict[str, Any]:
        """The record as plain data; money in `skip_currencies` (another owner's currency in the shared book) is left out."""
        return {
            "book": self.book.to_record(skip=skip_currencies),
            "memory": plain(self.memory),
            "currency": plain(self.currency),
            "cohorts": {key: plain(value) for key, value in sorted(self.cohorts.items())},
            "producers": {key: plain(value) for key, value in sorted(self.producers.items())},
            "merchants": {key: _merchant_record(value) for key, value in sorted(self.merchants.items())},
            "loans": [plain(loan) for loan in self.loans],
            "loan_requests": [plain(request) for request in self.loan_requests],
            "remembered_defaults": self.remembered_defaults,
            "credit_losses": self.credit_losses,
            "workforce": market_state_to_plain(self.workforce),
            "property_income": self.property_income,
            "volumes": self.volumes,
            "opening_basket": self.opening_basket,
            "expansion_runs": self.expansion_runs,
            "index_base_prices": self.index_base_prices,
            "worn_runs": self.worn_runs,
            "state_budget": plain(self.state_budget),
            "land_rent": self.land_rent,
            "margin_years": self.margin_years,
            "hours_hired": self.hours_hired,
            "funds_offered": self.funds_offered,
            "lent_by_borrower": self.lent_by_borrower,
            "curves": self.curves,
            "ways": {key: dict(built) for key, built in sorted(self.ways.items())},
        }

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "EconomyRecord":
        return cls(
            book=Book.from_record(record["book"]),
            memory=MarketMemory(**record["memory"]),
            currency=CurrencySpec(**record["currency"]),
            cohorts={key: Cohort(**value) for key, value in record["cohorts"].items()},
            producers={key: Producer(**value) for key, value in record["producers"].items()},
            merchants={key: _merchant_from(value) for key, value in record["merchants"].items()},
            loans=[Loan(**loan) for loan in record["loans"]],
            loan_requests=[LoanRequest(**request) for request in record["loan_requests"]],
            remembered_defaults=dict(record["remembered_defaults"]),
            credit_losses=dict(record["credit_losses"]),
            workforce=market_state_from_plain(record["workforce"]),
            property_income=dict(record["property_income"]),
            volumes=dict(record["volumes"]),
            opening_basket=dict(record["opening_basket"]),
            expansion_runs=dict(record["expansion_runs"]),
            index_base_prices=dict(record["index_base_prices"]),
            worn_runs=dict(record["worn_runs"]),
            state_budget=StateBudget(**record["state_budget"]),
            land_rent=dict(record["land_rent"]),
            margin_years=dict(record["margin_years"]),
            hours_hired=dict(record["hours_hired"]),
            funds_offered=record["funds_offered"],
            lent_by_borrower=dict(record["lent_by_borrower"]),
            curves=dict(record["curves"]),
            ways={key: dict(built) for key, built in record["ways"].items()},
        )


def _pair_keys(mapping: Dict[Tuple[str, str], Any]) -> Dict[str, Any]:
    return {first + KEY_SEPARATOR + second: value for (first, second), value in sorted(mapping.items())}


def _split_keys(mapping: Dict[str, Any]) -> Dict[Tuple[str, str], Any]:
    return {tuple(key.split(KEY_SEPARATOR, 1)): value for key, value in mapping.items()}


def _merchant_record(merchant: Merchant) -> Dict[str, Any]:
    return {"agent_id": merchant.agent_id, "home_tile": merchant.home_tile, "owner": merchant.owner,
            "capital_base": merchant.capital_base,
            "expected_prices": _pair_keys(merchant.expected_prices),
            "expected_volumes": _pair_keys(merchant.expected_volumes),
            "routes": {key: list(value) for key, value in _pair_keys(merchant.routes).items()}}


def _merchant_from(record: Dict[str, Any]) -> Merchant:
    return Merchant(agent_id=record["agent_id"], home_tile=record["home_tile"], owner=record["owner"],
                    capital_base=record["capital_base"],
                    expected_prices=_split_keys(record["expected_prices"]),
                    expected_volumes=_split_keys(record["expected_volumes"]),
                    routes={key: tuple(value) for key, value in _split_keys(record["routes"]).items()})
