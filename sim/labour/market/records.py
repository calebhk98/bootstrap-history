"""The plain records the labour-market core reads and writes.

People are counted per labour area, per trade and per ability band (aptitude.py). Money is whatever
unit the caller's wages and subsistence costs are given in; nothing here converts it. Every record is a
dataclass of numbers, strings, lists and dicts, so `to_plain`/`from_plain` round-trip a save without a
field list.
"""
import dataclasses
from typing import Callable, Dict, List, Optional, Sequence, Tuple

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
    expected_penalty: float = 0.0    # what a leaver expects to pay if the state recaptures him (money; the caller's rule)


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
    ask_floor_per_worker_year: Dict[AreaId, float] = dataclasses.field(default_factory=dict)  # the wage a worker needs to keep his household alive and working, less its own plot: the lowest an ask falls to
    value_of_life_years_of_income: float = 0.0          # prices a trade's fatality risk into its ask
    bondage_allowed: frozenset = frozenset()            # areas whose civilisation recognises bondage; others buy none
    bonded_for_sale: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)   # bonded people of a trade on offer in an area
    outlay_room: Dict[str, float] = dataclasses.field(default_factory=dict)   # money each employer's plan assigns to no line: with the wage line of its vacancies, all it may spend on bonded people (bonded_room.py)
    taxed_share: Dict[AreaId, float] = dataclasses.field(default_factory=dict)   # share of a worker's income the state takes from those who stay in the area, liability included
    fetch_wage: Optional[Callable] = None   # the kernel that prices fetched hands (fetch_wage.py); None: the reference, for a caller outside a game's assembly
    hours_share_at: Dict[Tuple[TradeId, AreaId], Callable[[float], float]] = dataclasses.field(default_factory=dict)   # (trade, area) -> share of the workers' hours they sell at a wage an hour (rising); absent: all of them, at any wage


@dataclasses.dataclass
class MarketState:
    """What the core carries from one year to the next.

    `workers[area][trade]` is people per ability band. `trainees[area][trade]` is a list of
    [years_left, people per band] for those still learning. `wages[area][trade]` is the market wage: the
    hours-weighted mean of what hours already held (at their contracts) and hours newly hired were paid."""
    workers: Dict[AreaId, Dict[TradeId, BandCounts]] = dataclasses.field(default_factory=dict)
    trainees: Dict[AreaId, Dict[TradeId, List[list]]] = dataclasses.field(default_factory=dict)
    wages: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)
    hired_hours: Dict[AreaId, Dict[TradeId, Dict[str, float]]] = dataclasses.field(default_factory=dict)
    entry_wages: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)   # the wage new hires cleared at last year: what the next year's offer moves from (`wages` is the mean over all hours held)
    contract_wages: Dict[AreaId, Dict[TradeId, Dict[str, float]]] = dataclasses.field(default_factory=dict)   # per employer, the mean wage an hour it holds is paid (clearing.contracted_wage)
    asks: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)   # ask over the reservation wage (asks.py)


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
    new_hire_wage: Optional[float] = None   # the wage hours hired new this year cleared at, before any premium (`wage` is the mean over all hours held, contracts included); none: the wage
    target_wage: Optional[float] = None   # where the wage is heading: toward the price where offered meets wanted hours, scaled by the imbalance; none: the wage
    hours_held: Optional[float] = None    # every hour the trade's workers here had at the clearing, sold or kept; none: not recorded
    demand: Tuple[Tuple[float, float], ...] = ()   # (maximum wage, hours) of each bid, the schedule the heading wage slides along as hands arrive

    @property
    def entry_wage(self) -> float:
        return self.wage if self.new_hire_wage is None else self.new_hire_wage

    @property
    def heading_wage(self) -> float:
        return self.wage if self.target_wage is None else self.target_wage

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
    formed: Dict[AreaId, Dict[TradeId, Dict[str, float]]] = dataclasses.field(default_factory=dict)   # first hands of an empty trade by route (formation.py)
    bonded_lots: list = dataclasses.field(default_factory=list)   # BondedLot rows: bonded people bought, from where, at what ask and carriage (bonded_worth.py)

    def clearing(self, trade: TradeId, area: AreaId) -> Optional[Clearing]:
        for each in self.clearings:
            if each.trade == trade and each.area == area:
                return each
        return None


_LEAF_TYPES = (float, int, str, bool, type(None))


def _plain_copy(value):
    """A copy of nested dicts, lists and tuples of numbers and strings, as `copy.deepcopy` makes it."""
    kind = type(value)
    if kind is dict:
        return {key: _plain_copy(item) for key, item in value.items()}
    if kind is list:
        return [item if type(item) in _LEAF_TYPES else _plain_copy(item) for item in value]
    if kind is tuple:
        return tuple(_plain_copy(item) for item in value)
    return value


def copy_state(state: MarketState) -> MarketState:
    """An independent copy of the state."""
    return MarketState(**{field.name: _plain_copy(getattr(state, field.name))
                          for field in dataclasses.fields(MarketState)})


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
