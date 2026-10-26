"""The state the coin module owns."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CoinWorld:
    # coin metal -> the market's price over the incumbents' cost as of the last year's close
    metal_ratios: Dict[str, float] = field(default_factory=dict)
