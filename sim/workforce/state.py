"""The state the workforce module owns: each seat's people and hours, and the society's labour hours."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

ONCE_COMMISSION = "commission"   # one-year orders by purpose: hours of a trade bought for this year only
ONCE_STOCK = "stock"             # the herds' growth labour
STAFF = "staff"     # version channel: the seat's people (employees, scholars, artisans, deputies, slaves, freedmen)


@dataclass
class TrainingRow:
    """One intake still learning: `people` of `trade` ready at `ready_year`; trade None is people the seat bought."""
    trade: Optional[str]
    people: float
    ready_year: float


@dataclass
class WorkforceSociety:
    society_labour_hours: Dict[str, float] = field(default_factory=dict)   # trade -> hours the society's workers of it give in a year
    # the unskilled hour's cleared wage at the last two clearings (the port notes it after each); the wage event reads the change
    cleared_wage: Optional[float] = None
    cleared_wage_before: Optional[float] = None


@dataclass
class WorkforceSeat:
    # ---- people ----
    scholars: float = 0.0
    artisans: float = 0.0
    directors_extra: float = 0.0
    employees: Dict[str, float] = field(default_factory=dict)
    slaves: int = 0
    freedmen: int = 0
    manumitted_total: int = 0
    # people trained or granted this year who are not yet in the labour core: trade -> people; the port puts them in before the clearing
    newcomers: Dict[str, float] = field(default_factory=dict)
    # spare generic hands the reserve_staff policy keeps above what concerns hold
    reserve_craftsmen: int = 0
    reserve_scholars: int = 0
    # the apprentices in training, one row per intake (sim/labour/labour_training.py)
    training: List[TrainingRow] = field(default_factory=list)
    trade_schools: Optional[Dict[str, float]] = None
    worker_housing_places: Optional[float] = None
    # the standing bid in the labour core: people wanted by trade (the places `hire` posts); `employees` is what the core hired last clearing
    staff_wanted: Dict[str, float] = field(default_factory=dict)
    # one-year orders in the labour core, purpose -> trade -> hours: posted with the standing places, cleared at the clearing;
    # `hours_hired_once` is what the last clearing hired for each purpose
    hours_wanted_once: Dict[str, Dict[str, float]] = field(default_factory=dict)
    hours_hired_once: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # the tile the household chose to operate from (None: the nation's default tile)
    base_tile: Optional[str] = None
    # how far the household's buying has bid up the people market; fades each year
    market_pressure: float = 0.0
    # ---- trades ----
    trades_created: Set[str] = field(default_factory=set)
    trades_endemic: Set[str] = field(default_factory=set)
    trade_introduced_year: Dict[str, int] = field(default_factory=dict)
    last_taught: Dict[str, int] = field(default_factory=dict)
    # ---- hours ----
    contract_hours: Dict[str, float] = field(default_factory=dict)
    teaching_hours_this_year: float = 0.0
    relocation_hours_this_year: float = 0.0
    supervision_hours_this_year: float = 0.0
    hour_allocations: Dict[str, float] = field(default_factory=dict)
    # standing order id -> [hours ordered, shortfall kind] last reported as unused, so repeats stay quiet
    unused_hours_reported: Dict[str, List[Any]] = field(default_factory=dict)
    work_trade: Optional[str] = None
    # hours of its own the seat offers in the labour core this year: trade -> hours; paid at the clearing, then spent
    hours_offered_for_wages: Dict[str, float] = field(default_factory=dict)
    wage_work_last_year: Optional[Dict[str, float]] = None
    hours_this_year: Optional[Dict[str, float]] = None
    trade_hours_used: Dict[str, float] = field(default_factory=dict)
    # ---- pay ----
    wages_paid: Optional[float] = None    # what the last clearing charged the seat for its staff and one-year orders; None before one
    said_deputies: int = 0

    @property
    def wage_hours_this_year(self) -> float:
        """Hours the seat has offered for wages since the last clearing: the total of its per-trade offers, which the clearing spends."""
        return sum(self.hours_offered_for_wages.values())
