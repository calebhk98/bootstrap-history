"""A seat: everything one player owns, held apart from the world.

The root `SimulationState.household`, `.projects` and `.founder` are aliases of the acting
seat's objects, so mechanism code keeps reading them; `bind_seat` points them at another seat.
"""
from dataclasses import dataclass
from typing import Optional

from sim.engine import state as state_module
from sim.engine.state import FounderState, HouseholdState, ProjectsState

FIRST_SEAT_ID = "founder"   # the one id the party-id constants agree on


@dataclass
class SeatState:
	"""One player's household, projects, founder and chosen win node."""
	household: HouseholdState
	projects: ProjectsState
	founder: Optional[FounderState] = None
	goal: Optional[str] = None


def bind_seat(state, seat_id: str) -> None:
	"""Point the root aliases at `seat_id`'s objects."""
	seat = state.seats[seat_id]
	state.acting_seat = seat_id
	state.household = seat.household
	state.projects = seat.projects
	state.founder = seat.founder


state_module.SeatState = SeatState   # the forward reference in SimulationState.seats
