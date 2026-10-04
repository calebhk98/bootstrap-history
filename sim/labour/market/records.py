"""The plain records the labour-market core reads and writes.

People are counted per labour area, per trade and per ability band (aptitude.py). Money is whatever
unit the caller's wages and subsistence costs are given in; nothing here converts it. Every record is a
dataclass of numbers, strings, lists and dicts, so `to_plain`/`from_plain` round-trip a save without a
field list.
"""
import dataclasses
from typing import Dict, List, Optional, Sequence

AreaId = str
TradeId = str
BandCounts = List[float]   # people per ability band, aligned with aptitude.band_abilities()


@dataclasses.dataclass(frozen=True)
class TradeSpec:
    """One trade as the core sees it. `difficulty` is in ability units (standard deviations of the
    population's aptitude): the ability at which half of those who start the training finish it."""
    trade_id: TradeId
    family: str
    training_years: float
    difficulty: float
    fatality_risk_per_year: float = 0.0
    fallback: bool = False          # work anyone can take up at once, without training


@dataclasses.dataclass(frozen=True)
class Bid:
    """An employer's demand for hours of one trade in one area.

    `maximum_wage` is the most an hour is worth to the employer: above it the employer hires nothing.
    `pay_premium` is the share over the market wage the employer chooses to pay; an employer paying more
    is filled first, takes hours from lower payers, and raises what the trade is known to pay there."""
    employer: str
    trade: TradeId
    area: AreaId
    hours: float
    maximum_wage: float
    pay_premium: float = 0.0


@dataclasses.dataclass(frozen=True)
class School:
    """Seats teaching one trade in one area, owned by any actor. A seat takes one trainee a year for the
    trade's training years; `completion_bonus` adds to every band's chance of finishing (better teaching),
    in ability units."""
    owner: str
    trade: TradeId
    area: AreaId
    seats: float
    completion_bonus: float = 0.0


@dataclasses.dataclass(frozen=True)
class Route:
    """One way out of an area: where it leads and what moving there costs a person, in money."""
    destination: AreaId
    moving_cost: float


@dataclasses.dataclass
class YearInputs:
    """What the world hands the core for one year. Anything missing for an area is taken as zero."""
    trades: Dict[TradeId, TradeSpec]
    bids: Sequence[Bid]
    subsistence_per_worker_year: Dict[AreaId, float]    # outside option: a worker and dependants at their floors
    hours_per_worker_year: float
    discount_rate: float
    career_years: float
    entrants: Dict[AreaId, float] = dataclasses.field(default_factory=dict)        # people coming of working age
    attrition_share: Dict[AreaId, float] = dataclasses.field(default_factory=dict)  # deaths and retirement a year
    routes: Dict[AreaId, List[Route]] = dataclasses.field(default_factory=dict)
    schools: Sequence[School] = ()
    enterable_trades: Optional[frozenset] = None        # None: every trade in `trades`
    value_of_life_years_of_income: float = 0.0          # prices a trade's fatality risk into its ask


@dataclasses.dataclass
class MarketState:
    """What the core carries from one year to the next.

    `workers[area][trade]` is people per ability band. `trainees[area][trade]` is a list of
    [years_left, people per band] for those still learning. `wages[area][trade]` is the market wage an
    hour last settled at (before any employer's premium)."""
    workers: Dict[AreaId, Dict[TradeId, BandCounts]] = dataclasses.field(default_factory=dict)
    trainees: Dict[AreaId, Dict[TradeId, List[list]]] = dataclasses.field(default_factory=dict)
    wages: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)
    hired_hours: Dict[AreaId, Dict[TradeId, Dict[str, float]]] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Clearing:
    """One (trade, area) market's year. `paid_by_employer` is the wage an hour each employer paid
    (the market wage times one plus its premium); `average_wage` is hours-weighted over everyone hired."""
    trade: TradeId
    area: AreaId
    wage: float
    hours_offered: float
    hours_wanted: float
    hours_hired: float
    hired_by_employer: Dict[str, float]
    paid_by_employer: Dict[str, float]
    average_wage: float

    @property
    def vacant_hours(self) -> float:
        return max(0.0, self.hours_wanted - self.hours_hired)

    @property
    def idle_hours(self) -> float:
        return max(0.0, self.hours_offered - self.hours_hired)

    @property
    def employment_share(self) -> float:
        """Share of offered hours hired: the chance an hour offered here finds work."""
        return self.hours_hired / self.hours_offered if self.hours_offered > 0.0 else 0.0


@dataclasses.dataclass
class YearReport:
    """What happened in the year, for screens, tests and the callers that pay wages."""
    clearings: List[Clearing] = dataclasses.field(default_factory=list)
    entered: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)
    switched: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)   # net, by trade
    migrated: Dict[AreaId, float] = dataclasses.field(default_factory=dict)                  # net, by area
    graduated: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)
    left_work: Dict[AreaId, float] = dataclasses.field(default_factory=dict)

    def clearing(self, trade: TradeId, area: AreaId) -> Optional[Clearing]:
        for each in self.clearings:
            if each.trade == trade and each.area == area:
                return each
        return None


def to_plain(state: MarketState) -> dict:
    return dataclasses.asdict(state)


def from_plain(plain: dict) -> MarketState:
    fields = {field.name for field in dataclasses.fields(MarketState)}
    return MarketState(**{name: value for name, value in plain.items() if name in fields})


def people_in(state: MarketState, area: Optional[AreaId] = None, include_trainees: bool = True) -> float:
    """Everyone the state counts, working or learning, in one area or all of them."""
    areas = [area] if area is not None else sorted(set(state.workers) | set(state.trainees))
    total = 0.0
    for each_area in areas:
        for bands in state.workers.get(each_area, {}).values():
            total += sum(bands)
        if include_trainees:
            for cohorts in state.trainees.get(each_area, {}).values():
                for cohort in cohorts:
                    total += sum(cohort[1])
    return total
