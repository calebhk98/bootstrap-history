"""What the markets module saves once per game."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MarketsWorld:
	agent_economy: Dict[str, Any] = field(default_factory=dict)   # the agent economy's record: its opening, its year's record and the traders' cargo legs
	# {"year", "drawn"}: the tonnes of each commodity each seat's running works drew from the goods market this year, by seat (the goods market writes them)
	market_flows: Optional[Dict[str, Any]] = None
	# whether the money an hour of work is worth is the agent economy's unskilled wage (set when the economy first opens and
	# the opening's money is repriced to it)
	money_from_economy: bool = False
