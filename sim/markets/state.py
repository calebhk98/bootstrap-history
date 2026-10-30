"""What the markets module saves once per game."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MarketsWorld:
	agent_economy: Dict[str, Any] = field(default_factory=dict)   # the agent economy's record: its opening, its year's record and the traders' cargo legs
	# commodity -> society capacity, stock and last price ratio (clearing.py)
	market_book: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# the year's purchases and sales by commodity and party, and the seat's draws (the goods market writes them)
	market_flows: Optional[Dict[str, Any]] = None
	# whether the money an hour of work is worth is the agent economy's unskilled wage (set when the economy first opens and
	# the opening's money is repriced to it)
	money_from_economy: bool = False
