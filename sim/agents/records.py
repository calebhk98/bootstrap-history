"""The persistent records of the actors other than the founder's household, and the loanable-funds market."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ActorRecord:
	"""Persistent state shared by every non-founder actor (a firm, a government)."""
	kind: str = "firm"
	name: str = ""
	policy_kind: str = "value"
	money: float = 0.0
	workforce: Dict[str, float] = field(default_factory=dict)
	knowledge: Set[str] = field(default_factory=set)
	concerns: Set[str] = field(default_factory=set)
	# node id -> copy work in progress (hours_left, money_left, years, ...)
	works: Dict[str, Dict[str, Any]] = field(default_factory=dict)
	failed_copies: Dict[str, int] = field(default_factory=dict)
	opened_year: Dict[str, int] = field(default_factory=dict)
	# node id -> how many times the concern's founding size the firm runs it at (absent = one)
	capacity: Dict[str, float] = field(default_factory=dict)
	target: Optional[str] = None
	location: Optional[str] = None
	exited_year: Optional[int] = None
	loss_years: int = 0
	founded_year: Optional[int] = None
	last_margin: float = 0.0
	# node id -> share of the concern's staff found in the labour pool last year
	staffing: Dict[str, float] = field(default_factory=dict)
	# purpose -> money in and out over the actor's life; money = income - outlays
	income: Dict[str, float] = field(default_factory=dict)
	outlays: Dict[str, float] = field(default_factory=dict)
	# a state's standing need by line last year, and the part it could not pay
	need: Dict[str, float] = field(default_factory=dict)
	unfunded: Dict[str, float] = field(default_factory=dict)
	# what the state seeks of the people it can see: share of income at full notice by kind of
	# claim, and the visible income those shares are spread over
	levy_requisition_rate: float = 0.0
	levy_office_rate: float = 0.0
	levy_base: float = 0.0
	# soldiers a state keeps now; 0 until its first year, when it holds the force it wants
	army: float = 0.0
	# a state's revenue last year by form, in money's worth, and the part of it taken in kind
	revenue_by_form: Dict[str, float] = field(default_factory=dict)
	revenue_in_kind: Dict[str, float] = field(default_factory=dict)
	# material -> tonnes the state took in kind last year, and tonnes it holds in store now
	in_kind_received: Dict[str, float] = field(default_factory=dict)
	stores: Dict[str, float] = field(default_factory=dict)
	# an interest group's kind (what hurt it), subject (the commodity or trade), what caused the
	# hurt in words, people it speaks for, the income it lost (net of what the state made good),
	# the share of the state's attention it commands, and what it asks of the state
	group_kind: str = ""
	subject: str = ""
	cause: str = ""
	members: float = 0.0
	lost_income: float = 0.0
	grievance: float = 0.0
	strength: float = 0.0
	peak_strength: float = 0.0
	claim: float = 0.0
	received_last_year: float = 0.0
	demands: List[str] = field(default_factory=list)
	petitions: int = 0
	last_logged_year: Optional[int] = None
	# what the treasury paid the founder as patron this year
	patron_grant: float = 0.0


@dataclass
class CapitalMarketRecord:
	"""A civilisation's loanable-funds market as it stood at its last yearly meeting."""
	# yearly market rate; 0 until the market has met, when the civilisation's starting rate stands
	rate: float = 0.0
	# funds demanded per unit held at the first meeting: the balance at which the rate is the starting rate
	reference_utilisation: float = 0.0
	# funds lenders hold, by source (households, firms, founder, state), and in all
	supply_by_source: Dict[str, float] = field(default_factory=dict)
	supply: float = 0.0
	# borrowing by the economy the simulation does not model actor by actor
	background: float = 0.0
	# what lenders will advance to modelled borrowers in all (before what is already lent)
	capacity: float = 0.0
	# actor id -> what it owed at the meeting
	loans: Dict[str, float] = field(default_factory=dict)
	# interest borrowers have paid and lenders not yet been paid; and running totals of each side
	interest_pool: float = 0.0
	interest_paid_total: float = 0.0
	interest_received_total: float = 0.0
	# the part of what lenders received that went to the society's savers (households, not modelled by actor)
	interest_to_households: float = 0.0


@dataclass
class ActorsState:
	"""Every actor other than the founder's household, keyed by actor id."""
	records: Dict[str, ActorRecord] = field(default_factory=dict)
	# civilisation id -> its loanable-funds market
	markets: Dict[str, CapitalMarketRecord] = field(default_factory=dict)
