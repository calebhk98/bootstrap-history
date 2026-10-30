"""The state the foreign-trade module owns: the partners' books, the lift ledgers and the actors' tallies."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ForeignTradeWorld:
    # partner id -> commodity -> its capacity, stock, reference demand, price ratio and last net trade (opened on first use)
    market_book: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
    # partner id -> material -> tonnes actors carried to and from it this year, and what the tonnes to it cost to land
    actor_trade: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
    # material -> tonnes actors landed in the home market and took from it this year
    home_actor_trade: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # partner id -> goods and coin paid, and the route's lift (rules.blank_ledger); a partner has one once a flow is settled
    ledgers: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # year -> value of goods this society imported ("in") and exported ("out") that year, in its money; the last few years
    trade_by_year: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # leg id -> the year's cargo leg a trader shipped, noted until the home market has cleared and settled once (empty between years)
    cargo: Dict[str, Dict[str, Any]] = field(default_factory=dict)
