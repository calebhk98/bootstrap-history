"""What the economy keeps about labour from year to year: the core's people, what households expect to sell, and who hired what."""
import math
from dataclasses import dataclass, field
from typing import Dict

from sim.labour.api import MarketState, market_state_from_plain, market_state_to_plain

from .market_memory import KEY_SEPARATOR
from .record_parts import OwnedRecord
from .types import AgentId, TradeId


@dataclass
class LabourRecord(OwnedRecord):
    workforce: MarketState = field(default_factory=MarketState)          # the labour core's state: people by labour area, trade and ability band, and the hours it hired
    hours_idle: Dict[str, float] = field(default_factory=dict)           # labour market_key -> hours offered and not hired last year (hours hired are the core's `workforce.hired_hours`, see `hours_hired_in`)
    hours_hired_by_employer: Dict[AgentId, Dict[TradeId, float]] = field(default_factory=dict)   # employer -> trade -> paid hours the last clearing hired for it
    sold_share_expected: Dict[str, float] = field(default_factory=dict)  # labour market_key -> share of offered hours households expect to sell, smoothed over the years (household_work_year.py)
    opening_sold_hours_per_worker: float = 0.0   # hours a working person was seeded to sell a year (zero: a whole working year)
    opening_sold_hours_by_area: Dict[str, float] = field(default_factory=dict)   # labour area -> hours a working person there was seeded to sell a year (empty: the one figure above)

    OWNERS = ("labour_record", "year_labour")
    AGENT_KEYED = ("hours_hired_by_employer",)
    ENCODERS = {"workforce": market_state_to_plain}
    DECODERS = {"workforce": market_state_from_plain}

    def hours_hired_in(self, market_key: str) -> float:
        """Hours the core's last clearing hired in the labour market `market_key` (trade, area), all employers."""
        trade, area = market_key.split(KEY_SEPARATOR, 1)
        return math.fsum(self.workforce.hired_hours.get(area, {}).get(trade, {}).values())

    def set_hours_hired_by_employer(self, hours: Dict[AgentId, Dict[TradeId, float]]) -> None:
        """The paid hours the last clearing hired for each employer, by trade."""
        self.hours_hired_by_employer = hours

    def expect_sold_share(self, market_key: str, share: float) -> None:
        """The share of offered hours households expect to sell in the market, where none is expected yet."""
        self.sold_share_expected.setdefault(market_key, share)

    def seed_sold_hours(self, per_worker: float, by_area: Dict[str, float]) -> None:
        """The hours a working person was seeded to sell a year, in all and by labour area."""
        self.opening_sold_hours_per_worker = per_worker
        self.opening_sold_hours_by_area = by_area

    def seed_workforce(self, workforce: MarketState) -> None:
        """The labour core's opening state."""
        self.workforce = workforce

    def seed_hired_hours(self, hired_hours) -> None:
        """The hours the opening contracts hold hired in the labour core."""
        self.workforce.hired_hours = hired_hours
