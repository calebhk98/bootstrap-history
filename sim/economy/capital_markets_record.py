"""What the capital markets keep from year to year: the banks households deposit with, who holds shares in which
producer, the dividends paid, hazards and insurance, and the property income households received."""
from dataclasses import dataclass, field
from typing import Dict, Optional

from .banks import Bank
from .capital_state import CapitalState
from .record_parts import OwnedRecord
from .types import AgentId


@dataclass
class CapitalMarketsRecord(OwnedRecord):
    banks: Dict[AgentId, Bank] = field(default_factory=dict)             # the banks households deposit with (banks.py)
    shares: Dict[AgentId, Dict[AgentId, float]] = field(default_factory=dict)   # producer -> holder -> part of its equity the holder bought (shares.py)
    last_dividends: Dict[AgentId, float] = field(default_factory=dict)   # producer -> the dividend it paid at its last close
    deposit_insurer: Optional[AgentId] = None                            # the actor that insures deposits, paid premiums by banks (deposit_insurance.py)
    last_resort: Optional[AgentId] = None                                # the actor that lends to a solvent bank facing a run (last_resort.py)
    last_resort_issues: bool = False                                     # whether that actor issues money (a bank of issue) or lends from its purse
    capital: CapitalState = field(default_factory=CapitalState)          # hazard records, insurers with their policies, and funds, keyed by AgentId (capital_state.py)
    property_income: Dict[AgentId, float] = field(default_factory=dict)  # dividends and interest last year
    pool_income: Dict[AgentId, float] = field(default_factory=dict)      # interest the actors' pool paid a lender since the last year's close, in the economy's unit

    last_pool_income: Dict[AgentId, float] = field(default_factory=dict)  # what the pool paid each lender at the last close, in the economy's unit

    OWNERS = ("capital_markets_record", "banks", "deposit_insurance", "last_resort", "funds", "insurance", "shares", "portfolio_year", "secondary_trade", "capital_year")
    AGENT_KEYED = ("banks", "shares", "last_dividends", "capital", "property_income", "pool_income", "last_pool_income")
    SAVED_SORTED = ("banks", "shares", "last_dividends")
    ENCODERS = {"capital": lambda capital: capital.to_plain()}
    DECODERS = {"banks": lambda value: {key: Bank(**each) for key, each in value.items()},
                "capital": CapitalState.from_plain}

    def designate_backstops(self, deposit_insurer: Optional[AgentId] = None, last_resort: Optional[AgentId] = None,
                           issues_money: bool = False) -> None:
        """The actor that insures deposits and the one that lends as a last resort (either may be absent)."""
        self.deposit_insurer, self.last_resort, self.last_resort_issues = deposit_insurer, last_resort, issues_money

    def set_property_income(self, income: Dict[AgentId, float]) -> None:
        """What households received as dividends, interest and rent."""
        self.property_income = dict(income)

    def take_pool_income(self) -> Dict[AgentId, float]:
        """The interest the actors' pool paid lenders since the last close; the close counts it in the year's income, once."""
        taken, self.pool_income = self.pool_income, {}
        self.last_pool_income = dict(taken)
        return taken

    def note_pool_income(self, agent: AgentId, amount: float) -> None:
        """The actors' pool paid `agent` (a lender of the economy) `amount` of interest; it joins the year's property income."""
        self.pool_income[agent] = self.pool_income.get(agent, 0.0) + amount

    def forget_producer(self, producer_id: AgentId) -> None:
        """The producer closed: nobody holds shares in it and it pays no dividend."""
        self.shares.pop(producer_id, None)
        self.last_dividends.pop(producer_id, None)
