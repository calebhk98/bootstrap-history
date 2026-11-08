"""The plain records the labour-market core reads and writes.

People are counted per labour area, per trade and per ability band (aptitude.py). Money is whatever
unit the caller's wages and subsistence costs are given in; nothing here converts it. Every record is a
dataclass of numbers, strings, lists and dicts, so `to_plain`/`from_plain` round-trip a save without a
field list.
"""
import dataclasses
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .carriage import carriage_costs, carriage_from, carriage_table
from .market_state import MarketState

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
class EmployerHoursBid:
    """An employer's demand for hours of one trade in one area.

    `maximum_wage` is the most an hour is worth to the employer: above it the employer hires nothing.
    Employers with a higher maximum are filled first and draw hours from lower ones."""
    employer: str
    trade: TradeId
    area: AreaId
    hours: float
    maximum_wage: float


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


def no_hours(wage: float) -> float:
    return 0.0


@dataclasses.dataclass
class YearInputs:
    """What the world hands the core for one year. Anything missing for an area is taken as zero."""
    trades: Dict[TradeId, TradeSpec]
    bids: Sequence[EmployerHoursBid]
    subsistence_per_worker_year: Dict[AreaId, float]    # outside option: a worker and dependants at their floors
    hours_per_worker_year: float
    discount_rate: float
    career_years: float
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
    hours_sold_at: Optional[Dict[Tuple[TradeId, AreaId], Callable[[float], float]]] = None   # (trade, area) -> hours the households there sell at a wage an hour (rising): the hours their offers hold. None: every worker sells a whole year at any wage; a market missing from a given schedule sells nothing

    _carriage: Dict[AreaId, Dict[AreaId, float]] = dataclasses.field(default_factory=dict, init=False, repr=False, compare=False)
    _costs: Optional[tuple] = dataclasses.field(default=None, init=False, repr=False, compare=False)

    def carriage_costs(self) -> tuple:
        """(areas the routes name, matrix of the cheapest moving cost between them; infinity: no way), searched once for the year."""
        if self._costs is None:
            self._costs = carriage_costs(self.routes)
        return self._costs

    def carriage_from(self, origin: AreaId) -> Dict[AreaId, float]:
        """The cheapest moving cost from `origin` to every area the routes lead to (`carriage.carriage_from`), searched once
        per origin for the year's routes; the answer is shared, read and never changed."""
        if not self._carriage and self.routes:
            self._carriage.update(carriage_table(self.routes))      # every origin in one search
        found = self._carriage.get(origin)
        if found is None:
            found = self._carriage[origin] = carriage_from(self.routes, origin)      # an area no way starts from
        return found

    def sold_schedule(self, trade: TradeId, area: AreaId) -> Optional[Callable[[float], float]]:
        """The hours sold at a wage in one market; None where no schedule is given (the workers' whole year is sold)."""
        if self.hours_sold_at is None:
            return None
        return self.hours_sold_at.get((trade, area), no_hours)

    def hours_sold(self, trade: TradeId, area: AreaId, workers_hours: float, wage: float) -> float:
        """Hours sold in a market at a wage, given the hours its workers have in all."""
        schedule = self.sold_schedule(trade, area)
        return workers_hours if schedule is None else schedule(wage)


@dataclasses.dataclass
class LabourClearing:
    """One (trade, area) market's year. `wage` is the one wage an hour every employer pays, held hours and new alike:
    what the hours taken on were paid, before any premium."""
    trade: TradeId
    area: AreaId
    wage: float
    hours_offered: float
    hours_wanted: float
    hours_hired: float
    hired_by_employer: Dict[str, float]
    target_wage: Optional[float] = None   # where the wage is heading: toward the price where offered meets wanted hours, scaled by the imbalance; none: the wage
    hours_held: Optional[float] = None    # every hour the trade's workers here had at the clearing, sold or kept; none: not recorded
    demand: Tuple[Tuple[float, float], ...] = ()   # (maximum wage, hours) of each bid, the schedule the heading wage slides along as hands arrive

    @property
    def heading_wage(self) -> float:
        return self.wage if self.target_wage is None else self.target_wage

    @property
    def vacant_hours(self) -> float:
        return max(0.0, self.hours_wanted - self.hours_hired)

    @property
    def idle_hours(self) -> float:
        return max(0.0, self.hours_offered - self.hours_hired)


@dataclasses.dataclass
class YearReport:
    """What happened in the year, for screens, tests and the callers that pay wages."""
    clearings: List[LabourClearing] = dataclasses.field(default_factory=list)
    switched: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)   # net, by trade
    migrated: Dict[AreaId, float] = dataclasses.field(default_factory=dict)                  # net, by area
    graduated: Dict[AreaId, Dict[TradeId, float]] = dataclasses.field(default_factory=dict)
    formed: Dict[AreaId, Dict[TradeId, Dict[str, float]]] = dataclasses.field(default_factory=dict)   # first hands of an empty trade by route (formation.py)
    bonded_lots: list = dataclasses.field(default_factory=list)   # BondedLot rows: bonded people bought, from where, at what ask and carriage (bonded_worth.py)

    def clearing(self, trade: TradeId, area: AreaId) -> Optional[LabourClearing]:
        for each in self.clearings:
            if each.trade == trade and each.area == area:
                return each
        return None


def copy_state(state: MarketState) -> MarketState:
    """An independent copy of the state."""
    return state.copy()


def to_plain(state: MarketState) -> dict:
    return state.to_plain()


def from_plain(plain: dict) -> MarketState:
    names = ("workers", "trainees", "wages", "hired_hours", "asks")
    return MarketState(**{name: value for name, value in plain.items() if name in names})


def people_in(state: MarketState, area: Optional[AreaId] = None, include_trainees: bool = True) -> float:
    """Everyone the state counts, working or learning, in one area or all of them."""
    if area is not None:
        return state.area_people(area, include_trainees)
    total = 0.0
    for each_area in state.ids.areas.names:
        total += state.area_people(each_area, include_trainees)
    return total
