"""The state the workforce module owns: each seat's people and hours, and the society's labour hours."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

STAFF = "staff"     # version channel: the seat's people (employees, scholars, artisans, deputies, slaves, freedmen)


@dataclass
class WorkforceSociety:
    society_labour_hours: Dict[str, float] = field(default_factory=dict)   # trade -> hours the society's workers of it give in a year
    wage_tightness_factors: Dict[str, float] = field(default_factory=dict)  # trade -> how far its wage has been pushed by scarcity


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
    # staff an institution granted outright: {"scholars": n, "artisans": n} (made when first granted)
    granted_staff: Optional[Dict[str, float]] = None
    # spare generic hands the reserve_staff policy keeps above what concerns hold
    reserve_craftsmen: int = 0
    reserve_scholars: int = 0
    # the apprentices in training, one row per intake (sim/labour/labour_training.py)
    training: List[List[Any]] = field(default_factory=list)
    trade_schools: Optional[int] = None
    worker_housing_places: Optional[int] = None
    # yearly pay per person by trade as last settled; follows the market while keep_pay_at_market is on
    staff_pay_held: Dict[str, float] = field(default_factory=dict)
    # the tile the household chose to operate from (None: the nation's default tile)
    base_tile: Optional[str] = None
    # how far the household's buying has bid up the people market; fades each year
    market_pressure: float = 0.0
    # ---- trades ----
    trades_created: Set[str] = field(default_factory=set)
    trades_endemic: Set[str] = field(default_factory=set)
    trade_introduced_year: Dict[str, int] = field(default_factory=dict)
    last_taught: Dict[str, int] = field(default_factory=dict)
    labour_pressure_records: Dict[str, Any] = field(default_factory=dict)
    # ---- hours ----
    contract_hours: Dict[str, float] = field(default_factory=dict)
    commissioned: Dict[str, float] = field(default_factory=dict)
    teaching_hours_this_year: float = 0.0
    relocation_hours_this_year: float = 0.0
    supervision_hours_this_year: float = 0.0
    hour_allocations: Dict[str, float] = field(default_factory=dict)
    # standing order id -> [hours ordered, shortfall kind] last reported as unused, so repeats stay quiet
    unused_hours_reported: Dict[str, List[Any]] = field(default_factory=dict)
    work_trade: Optional[str] = None
    wage_hours_this_year: float = 0.0
    wage_income_this_year: float = 0.0
    wage_work_last_year: Optional[Dict[str, float]] = None
    hours_this_year: Optional[Dict[str, float]] = None
    trade_hours_used: Dict[str, float] = field(default_factory=dict)
    director_hours_spent_founder: float = 0.0
    # ---- pay ----
    wages_paid: float = 0.0
    wages_prepaid: float = 0.0
    wages_earned: Optional[float] = None
    living_cost_paid: float = 0.0
    said_deputies: int = 0
