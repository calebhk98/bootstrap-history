"""A seat: everything one player owns, held apart from the world.

The acting seat's record is `SimulationState.acting_record`; `bind_seat` names another seat the acting one.
What the seats module knows of the seat (goal, country, kind, holder, policy, the founder's life) is its slot in `modules`.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from sim.engine import state as state_module
from sim.engine.state import FounderState, HouseholdState
from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.knowledge.api import KnowledgeSeat
from sim.seats.api import COUNTRY_SEAT, SeatsSeat
from sim.workforce.api import WorkforceSeat

FIRST_SEAT_ID = "founder"   # the one id the party-id constants agree on
FOUNDER_SECTION = "founder"   # the seat section (and reply key) holding the founder, absent for a country seat


@dataclass
class SeatState:
	"""One player's household, founder record, holdings and progress record, and the state of every module that keeps some per seat."""
	household: HouseholdState
	founder: Optional[FounderState] = None
	holdings: HoldingsState = field(default_factory=HoldingsState)
	seat_progress: SeatProgressState = field(default_factory=SeatProgressState)
	modules: Dict[str, Any] = field(default_factory=dict)   # module id -> this seat's state (sim/assembly slots)


def seat_from_template(template: Mapping[str, Any], policy: Dict[str, Any]) -> SeatState:
	"""A new seat from data: `template` may carry `starting_techs`, `scholars`, `artisans`, `base_tile`, `goal` and
	`country`. Its money is opened by the ledger once the seat is in the registry."""
	if template.get("kind") == COUNTRY_SEAT:
		# the household here is an empty placeholder; the seat acts through its government
		return SeatState(household=HouseholdState(), founder=None,
		                 modules={"seats": SeatsSeat(country=template.get("country"), kind=COUNTRY_SEAT)})
	household = HouseholdState()
	granted = set(template.get("starting_techs") or ())
	founder = FounderState()
	staff = WorkforceSeat(scholars=float(template.get("scholars", 0.0)), artisans=float(template.get("artisans", 0.0)),
	                      base_tile=template.get("base_tile"))
	return SeatState(household=household, founder=founder, modules={
		"workforce": staff, "knowledge": KnowledgeSeat(done=set(granted), granted=set(granted)),
		"seats": SeatsSeat(goal=template.get("goal"), country=template.get("country"), policy=dict(policy))})


def bind_seat(state, seat_id: str) -> None:
	"""Name `seat_id` the acting seat."""
	if seat_id not in state.seats:
		raise KeyError(seat_id)
	state.acting_seat = seat_id


state_module.SeatState = SeatState   # the forward reference in SimulationState.seats
