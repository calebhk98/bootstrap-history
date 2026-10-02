"""Everything one economy carries from year to year, and its round trip to plain JSON for the save.

The book holds money and goods; the agents' records hold what they expect and plan; the memory
holds last year's market outcomes. Nothing else survives a year.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .accounts import Book
from .households_cohort import Cohort
from .market_memory import KEY_SEPARATOR, MarketMemory
from .merchants import Merchant
from .producers import Producer
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
    workforce: Dict[TileId, Dict[TradeId, float]] = field(default_factory=dict)   # workers by tile and trade
    property_income: Dict[AgentId, float] = field(default_factory=dict)  # dividends and interest last year
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> last year's quantity
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening
    expansion_runs: Dict[AgentId, float] = field(default_factory=dict)   # capacity a loan request would build
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    worn_runs: Dict[AgentId, float] = field(default_factory=dict)        # plant that wore out last year, to rebuild
    state_budget: StateBudget = field(default_factory=StateBudget)       # the state's revenue and this year's plan

    def to_record(self) -> Dict[str, Any]:
        return {
            "book": self.book.to_record(),
            "memory": dataclasses.asdict(self.memory),
            "currency": dataclasses.asdict(self.currency),
            "cohorts": {key: dataclasses.asdict(value) for key, value in sorted(self.cohorts.items())},
            "producers": {key: dataclasses.asdict(value) for key, value in sorted(self.producers.items())},
            "merchants": {key: _merchant_record(value) for key, value in sorted(self.merchants.items())},
            "loans": [dataclasses.asdict(loan) for loan in self.loans],
            "loan_requests": [dataclasses.asdict(request) for request in self.loan_requests],
            "workforce": self.workforce,
            "property_income": self.property_income,
            "volumes": self.volumes,
            "opening_basket": self.opening_basket,
            "expansion_runs": self.expansion_runs,
            "index_base_prices": self.index_base_prices,
            "worn_runs": self.worn_runs,
            "state_budget": dataclasses.asdict(self.state_budget),
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
            workforce={tile: dict(trades) for tile, trades in record["workforce"].items()},
            property_income=dict(record["property_income"]),
            volumes=dict(record["volumes"]),
            opening_basket=dict(record["opening_basket"]),
            expansion_runs=dict(record["expansion_runs"]),
            index_base_prices=dict(record["index_base_prices"]),
            worn_runs=dict(record["worn_runs"]),
            state_budget=StateBudget(**record["state_budget"]),
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
