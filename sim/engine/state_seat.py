"""A seat: everything one player owns, held apart from the world.

The root `SimulationState` fields `household`, `projects`, `founder`, `holdings`, `governance` and
`seat_progress` are aliases of the acting seat's objects, so mechanism code keeps reading them; `bind_seat` points them at another seat.
"""
from dataclasses import dataclass, field
from typing import Optional

from sim.engine import state as state_module
from sim.engine.state import FounderState, GovernanceState, HouseholdState, ProjectsState
from sim.engine.state_holdings import HoldingsState, SeatProgressState

FIRST_SEAT_ID = "founder"   # the one id the party-id constants agree on


@dataclass
class SeatState:
	"""One player's household, projects, founder, holdings, institutions, goal record and chosen win node."""
	household: HouseholdState
	projects: ProjectsState
	founder: Optional[FounderState] = None
	holdings: HoldingsState = field(default_factory=HoldingsState)
	governance: GovernanceState = field(default_factory=GovernanceState)
	seat_progress: SeatProgressState = field(default_factory=SeatProgressState)
	goal: Optional[str] = None


def bind_seat(state, seat_id: str) -> None:
	"""Point the root aliases at `seat_id`'s objects."""
	seat = state.seats[seat_id]
	state.acting_seat = seat_id
	state.household = seat.household
	state.projects = seat.projects
	state.founder = seat.founder
	state.holdings = seat.holdings
	state.governance = seat.governance
	state.seat_progress = seat.seat_progress


state_module.SeatState = SeatState   # the forward reference in SimulationState.seats
