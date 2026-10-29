"""A seat: everything one player owns, held apart from the world.

The root `SimulationState` fields `household`, `projects`, `founder`, `holdings` and
`seat_progress` are aliases of the acting seat's objects, so mechanism code keeps reading them; `bind_seat` points them at another seat.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from sim.engine import state as state_module
from sim.engine.state import FounderState, HouseholdState, ProjectsState
from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.workforce.api import WorkforceSeat

FIRST_SEAT_ID = "founder"   # the one id the party-id constants agree on
FOUNDER_SECTION = "founder"   # the seat section (and reply key) holding the founder, absent for a country seat
HOUSEHOLD_SEAT = "household"
COUNTRY_SEAT = "country"


@dataclass
class SeatState:
	"""One player's household, projects, founder, holdings, institutions, goal record and chosen win node."""
	household: HouseholdState
	projects: ProjectsState
	founder: Optional[FounderState] = None
	holdings: HoldingsState = field(default_factory=HoldingsState)
	seat_progress: SeatProgressState = field(default_factory=SeatProgressState)
	goal: Optional[str] = None
	country: Optional[str] = None   # the civilisation id the seat belongs to; None is the game's own country
	kind: str = HOUSEHOLD_SEAT      # COUNTRY_SEAT: the holder is that country's government, with no founder and no household of its own
	holder: Optional[str] = None    # a country seat's government actor id; a household seat's holder is its household
	modules: Dict[str, Any] = field(default_factory=dict)   # module id -> this seat's state (sim/assembly slots)

	@property
	def holds_household(self) -> bool:
		return self.kind != COUNTRY_SEAT


def seat_from_template(template: Mapping[str, Any], capital: float, policy: Dict[str, Any]) -> SeatState:
	"""A new seat from data: `template` may carry `starting_techs`, `scholars`, `artisans`, `base_tile`, `goal` and
	`country`. `capital` is already in the society's coin."""
	if template.get("kind") == COUNTRY_SEAT:
		# the household here is an empty placeholder the engine's aliases need; the seat acts through its government
		return SeatState(household=HouseholdState(capital=0.0), projects=ProjectsState(), founder=None,
		                 country=template.get("country"), kind=COUNTRY_SEAT)
	household = HouseholdState(capital=float(capital))
	granted = set(template.get("starting_techs") or ())
	projects = ProjectsState(done=set(granted), granted=set(granted))
	founder = FounderState(policy=dict(policy))
	staff = WorkforceSeat(scholars=float(template.get("scholars", 0.0)), artisans=float(template.get("artisans", 0.0)),
	                      base_tile=template.get("base_tile"))
	return SeatState(household=household, projects=projects, founder=founder, goal=template.get("goal"),
	                 country=template.get("country"), modules={"workforce": staff})


def bind_seat(state, seat_id: str) -> None:
	"""Point the root aliases at `seat_id`'s objects."""
	seat = state.seats[seat_id]
	state.acting_seat = seat_id
	state.household = seat.household
	state.projects = seat.projects
	state.founder = seat.founder
	state.holdings = seat.holdings
	state.seat_progress = seat.seat_progress


state_module.SeatState = SeatState   # the forward reference in SimulationState.seats
