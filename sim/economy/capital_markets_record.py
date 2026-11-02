"""What the capital markets keep from year to year: the banks households deposit with, who holds shares in which
producer, the dividends paid, hazards and insurance, and the property income households received."""
from dataclasses import dataclass, field
from typing import Dict

from .banks import Bank
from .capital_state import CapitalState
from .record_parts import OwnedRecord
from .types import AgentId


@dataclass
class CapitalMarketsRecord(OwnedRecord):
    banks: Dict[AgentId, Bank] = field(default_factory=dict)             # the banks households deposit with (banks.py)
    shares: Dict[AgentId, Dict[AgentId, float]] = field(default_factory=dict)   # producer -> holder -> part of its equity the holder bought (shares.py)
    last_dividends: Dict[AgentId, float] = field(default_factory=dict)   # producer -> the dividend it paid at its last close
    capital: CapitalState = field(default_factory=CapitalState)          # hazard records, insurers with their policies, and funds, keyed by AgentId (capital_state.py)
    property_income: Dict[AgentId, float] = field(default_factory=dict)  # dividends and interest last year

    AGENT_KEYED = ("banks", "shares", "last_dividends", "capital", "property_income")
    SAVED_SORTED = ("banks", "shares", "last_dividends")
    ENCODERS = {"capital": lambda capital: capital.to_plain()}
    DECODERS = {"banks": lambda value: {key: Bank(**each) for key, each in value.items()},
                "capital": CapitalState.from_plain}
