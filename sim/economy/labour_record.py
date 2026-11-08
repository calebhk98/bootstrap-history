"""What the economy keeps about labour from year to year: the core's people, what households expect to sell, and who hired what."""
import math
from dataclasses import dataclass, field
from typing import Dict

from sim.labour.api import MarketState, add_people, grid_rows_of, hours_cleared_at, market_state_from_plain, market_state_to_plain

from .market_memory import KEY_SEPARATOR
from .record_parts import OwnedRecord
from .types import AgentId, TradeId


@dataclass
class LabourRecord(OwnedRecord):
    workforce: MarketState = field(default_factory=MarketState)          # the labour core's state: people by labour area, trade and ability band, and the hours it hired
    hours_idle: Dict[str, float] = field(default_factory=dict)           # labour market_key -> hours offered and not hired by last year's clearing (the hours it did hire: `hours_cleared_in`)
    hours_paid_by_employer: Dict[AgentId, Dict[TradeId, float]] = field(default_factory=dict)   # employer -> trade -> hours paid for last year, bonded hours included (the staff the employer worked with; the clearing's own hours are `hours_cleared_in`)
    sold_share_expected: Dict[str, float] = field(default_factory=dict)  # labour market_key -> share of offered hours households expect to sell, smoothed over the years (household_work_year.py)
    opening_sold_hours_per_worker: float = 0.0   # hours a working person was seeded to sell a year (zero: a whole working year)
    opening_sold_hours_by_area: Dict[str, float] = field(default_factory=dict)   # labour area -> hours a working person there was seeded to sell a year (empty: the one figure above)

    OWNERS = ("labour_record", "year_labour")
    AGENT_KEYED = ("hours_paid_by_employer",)
    ENCODERS = {"workforce": market_state_to_plain}
    DECODERS = {"workforce": market_state_from_plain}

    def sold_hours_per_worker(self, default: float):
        """The hours a working person was seeded to sell a year: the figure per labour area, else the one figure, else
        `default` (a whole working year). A float or a mapping (opening_placement.HoursPerWorker)."""
        return self.opening_sold_hours_by_area or self.opening_sold_hours_per_worker or default

    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """`old` becomes `new` as an employer in the core's hired hours as well as in the stores keyed by an agent id."""
        super().rename_agent(old, new)
        self.workforce.rename_employer(old, new)

    def hours_cleared_in(self, market_key: str) -> float:
        """Hours the core's last clearing hired in the labour market `market_key` (trade, area), all employers: before
        payment and without bonded hours, so with `hours_idle` they make up the hours offered."""
        trade, area = market_key.split(KEY_SEPARATOR, 1)
        return self.hours_cleared_by(trade, area)

    def hours_cleared_by(self, trade: str, area: str) -> float:
        """`hours_cleared_in` for a market already split into its trade and labour area."""
        return float(hours_cleared_at(self.workforce, grid_rows_of(self.workforce, [area], [trade]))[0])

    def hours_cleared_in_markets(self, market_keys) -> list:
        """`hours_cleared_in` for many market keys at once, in their order."""
        trades, areas = [], []
        for market_key in market_keys:
            trade, area = market_key.split(KEY_SEPARATOR, 1)
            trades.append(trade)
            areas.append(area)
        return hours_cleared_at(self.workforce, grid_rows_of(self.workforce, areas, trades)).tolist()

    def set_hours_paid_by_employer(self, hours: Dict[AgentId, Dict[TradeId, float]]) -> None:
        """The hours paid for each employer, by trade, bonded hours included."""
        self.hours_paid_by_employer = hours

    def expect_sold_share(self, market_key: str, share: float) -> None:
        """The share of offered hours households expect to sell in the market, where none is expected yet."""
        self.sold_share_expected.setdefault(market_key, share)

    def seed_sold_hours(self, per_worker: float, by_area: Dict[str, float]) -> None:
        """The hours a working person was seeded to sell a year, in all and by labour area."""
        self.opening_sold_hours_per_worker = per_worker
        self.opening_sold_hours_by_area = by_area

    def add_workers(self, area: str, trade: TradeId, people: float) -> None:
        """People placed in `trade` from outside the clearing (a seat's apprentices, staff an institution granted). They
        live in the area already, so demography counts them: they leave the area's other trades, each in proportion to
        its workers, and the area's headcount is unchanged. Where the other trades hold fewer than that, the rest are
        added, and the next year's following of demography (`Economy._follow_population`) scales the area back."""
        take_from_other_trades(self.workforce.workers.get(area, {}), trade, people)
        add_people(self.workforce, area, trade, people)

    def seed_workforce(self, workforce: MarketState) -> None:
        """The labour core's opening state."""
        self.workforce = workforce

    def seed_hired_hours(self, hired_hours) -> None:
        """The hours the opening contracts hold hired in the labour core."""
        self.workforce.hired_hours = hired_hours


def take_from_other_trades(workers_by_trade: Dict[TradeId, list], trade: TradeId, people: float) -> float:
    """Take `people` from the trades other than `trade`, each in proportion to its workers and each band in proportion
    to the trade's bands; at most everyone they hold. Returns the people taken."""
    others = {other: bands for other, bands in sorted(workers_by_trade.items()) if other != trade}
    held = math.fsum(sum(bands) for bands in others.values())
    if held <= 0.0 or people <= 0.0:
        return 0.0
    share = min(1.0, people / held)
    for bands in others.values():
        for index, band in enumerate(bands):
            bands[index] = band * (1.0 - share)
    return held * share
