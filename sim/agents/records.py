"""The persistent records of the actors other than the founder's household, and the loanable-funds market."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .edges import Edge
from .purses import Purses


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
	# a state's works in stock by name (m2 of masonry equivalent), the grain price it takes as normal, and whether
	# a new ruler has acceded whose donative is still to be paid
	works_stock: Dict[str, float] = field(default_factory=dict)
	grain_price_reference: float = 0.0
	accession_due: bool = False
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
	# how the actor answers the state's demands ("comply" or "refuse", sim/agents/demand_answer.py)
	demand_stance: str = "comply"
	# a state's goods it will not sell abroad (its monopolies, set at the start by its country's data), and
	# the parties it has shut its markets to: party id -> the first year they are open to them again
	state_monopolies: Set[str] = field(default_factory=set)
	closed_markets: Dict[str, int] = field(default_factory=dict)
	# material -> units of the state's stock that smugglers have taken, which it can no longer sell
	stock_taken: Dict[str, float] = field(default_factory=dict)
	# ---- every actor: the country whose government it answers to and whose techniques it starts
	# with (None = the home country), and who drives it ("ai", "human", "llm")
	country: Optional[str] = None
	controller: str = "ai"

	# ---- a player: commands waiting for its next turn, and what happened to the ones it gave
	orders: List[Dict[str, Any]] = field(default_factory=list)
	journal: List[Dict[str, Any]] = field(default_factory=list)
	# node id -> what each concern a player runs made last year, after levy and royalty
	margins: Dict[str, float] = field(default_factory=dict)

	# ---- a trader: route key -> what it has committed there (cargo, capital, last margin, ...)
	routes: Dict[str, Dict[str, Any]] = field(default_factory=dict)

	# ---- a stratum: which body of people it is, their literacy share, last year's unmet share of
	# each need, and last year's growth rate of `members`
	stratum: str = ""
	literacy: float = 0.0
	shortfall: Dict[str, float] = field(default_factory=dict)
	last_growth: float = 0.0
	# its definition as data (name, share, trade, property_share, bonded, owner, rises_to, falls_to,
	# ...), last year's welfare ratio, what its keepers handed it for the year, and the people it
	# has decided to send to another stratum this year (stratum id -> people), settled by the registry
	plan: Dict[str, Any] = field(default_factory=dict)
	welfare: float = 0.0
	allowance: float = 0.0
	# a bonded stratum: the value of this year's work, owed to its keeper at settlement
	labour_product: float = 0.0
	moving: Dict[str, float] = field(default_factory=dict)

	# ---- exchange: offers other actors have made to this one, and how many it has made itself
	offers: List[Dict[str, Any]] = field(default_factory=list)
	offer_serial: int = 0

	# ---- coinage policy (a state): the share of its coin's metal it chose to cut this year, and the
	# share of the opening metal its coin still holds after every cut so far
	coin_cut_share: float = 0.0
	coin_metal_kept: float = 1.0

	# ---- patents and company shares: node id -> {"granted", "expires", "licensees"} for the exclusive
	# rights the actor holds; actor id -> share it holds in that actor's equity; and the share of
	# its own equity the actor has issued to others (the rest is its own)
	patents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
	holdings: Dict[str, float] = field(default_factory=dict)
	issued: float = 0.0
	# node id -> {"holder", "rate"}: the royalty on its takings from a concern the actor runs under a licence
	royalty_owed: Dict[str, Dict[str, Any]] = field(default_factory=dict)

	# ---- a firm founded by staff leaving another: the parent's id, empty otherwise
	spun_off_from: str = ""

	# ---- a state's tax on bodies of people: stratum id -> the earned income (cumulative) it has
	# already assessed, so each year's income is assessed once
	income_assessed: Dict[str, float] = field(default_factory=dict)

	# ---- firm entry and exit: consecutive years a firm earned less than its plant would lend for
	weak_years: int = 0

	# ---- an interest group of strata: the share of its loss the founder is blamed for; and a stratum's
	# remembered welfare (what it has come to expect)
	blame_share: float = 1.0
	welfare_reference: float = 0.0
	# what a stratum has come to expect of each income it earns (wages, property) and a firm of its profit
	income_reference: Dict[str, float] = field(default_factory=dict)
	margin_reference: float = 0.0


@dataclass
class CountryProfile:
	"""What one country starts a game with: read from its civilisation file when the cast is seeded,
	then saved with the game, so every save keeps the countries it began with."""
	country: str = ""
	name: str = ""
	population: float = 0.0
	urban_fraction: float = 0.0
	state_capacity: float = 0.0
	tax_share: float = 0.0
	wage_index: float = 1.0
	price_index: float = 1.0
	literacy_general: float = 0.0
	literacy_elite: float = 0.0
	home_tiles: List[str] = field(default_factory=list)
	# where the country is on the map (a tile or region id the world can measure distance to)
	location: Optional[str] = None
	# the techniques the country knows at the start: its actors' baseline tree
	starting_techs: Set[str] = field(default_factory=set)
	# bodies of people the country starts with, as data ({"name", "share", "income", ...}); empty
	# means derive them from what the world can see
	strata: List[Dict[str, Any]] = field(default_factory=list)
	# anything else the scenario or a mod declares for the country
	extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CastEntry:
	"""One actor a scenario starts with: who it is, what kind, whose country, who drives it."""
	actor_id: str = ""
	kind: str = "government"
	country: Optional[str] = None
	name: str = ""
	controller: str = "ai"
	policy_kind: str = "value"
	money: float = 0.0
	location: Optional[str] = None
	# anything else the kind reads when it is created
	params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActorsState:
	"""Every actor other than the founder's household, keyed by actor id."""
	records: Dict[str, ActorRecord] = field(default_factory=dict)
	# the game's roster as seeded at its first actor year, and the countries in it; empty until then
	cast: Dict[str, CastEntry] = field(default_factory=dict)
	countries: Dict[str, CountryProfile] = field(default_factory=dict)
	# the founder's own country (the civilisation the game was started with)
	home_country: str = ""
	# every actor's money, as accounts in a book with the edges among them, and the debts as loan claims (purses.py)
	purses: Any = field(default_factory=Purses)
	# named edge -> material -> tonnes of goods it holds (stolen stock goes to the thieves' edge)
	edge_goods: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# concern id -> the takings of a lone operator that entrants expect, and the year it was last revised
	expected_takings: Dict[str, float] = field(default_factory=dict)
	expected_takings_year: Dict[str, int] = field(default_factory=dict)

	def __post_init__(self) -> None:
		if isinstance(self.purses, dict):
			self.purses = Purses.from_record(self.purses)

	def edge(self, name: str) -> Edge:
		"""The named edge, an account outside the actors that a posting can name as its counterparty."""
		return Edge(name, self.purses, self.edge_goods)
