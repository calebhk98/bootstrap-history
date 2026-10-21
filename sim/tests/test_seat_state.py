"""A seat holds one player's household, projects, founder and goal; the root fields alias the acting seat. The rules are
called on a `SimulationState` and on the real `SeatMixin` over a stub (no household facade is built); the checks on a
whole Rome game's save and load are test_seat_state_scenario."""

QUICK_TOPIC = True

from .harness import check

from sim.engine.core_seats import SeatMixin
from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState


class Seats(SeatMixin):
    """The seat switching of a game over a bare state: each seat's facade is a marker object."""

    def __init__(self, state):
        self.state = state
        self._seat_facades = {seat_id: object() for seat_id in state.seats}
        self.household = self._seat_facades[state.acting_seat]
        self.resets = 0

    def _new_facade(self, seat_id):
        return object()

    def _reset_economic_caches(self):
        self.resets += 1


household = HouseholdState(capital=1000.0)
state = SimulationState(household=household, projects=ProjectsState(), founder=FounderState())
first = state.seats[FIRST_SEAT_ID]

check("one seat exists and is acting", list(state.seats) == [FIRST_SEAT_ID] and state.acting_seat == FIRST_SEAT_ID, list(state.seats))
check("the root household, projects and founder are the acting seat's objects",
      state.household is first.household and state.projects is first.projects and state.founder is first.founder, None)
state._goal = "point_contact_transistor"
check("the root goal is the acting seat's goal", first.goal == "point_contact_transistor", first.goal)

# a second seat: switching rebinds the aliases and the facade, and restores on exit and on error
game = Seats(state)
second_household = HouseholdState(capital=50.0)
game.add_seat("second", SeatState(household=second_household, projects=ProjectsState(), founder=FounderState()))
first_facade = game.household
with game.act_as("second"):
    check("inside act_as the root household is the second seat's",
          state.household is second_household and state.household.capital == 50.0, state.household.capital)
    check("each seat has its own household facade", game.household is not first_facade, None)
    check("the second seat has no goal of its own", state._goal is None, state._goal)
check("leaving act_as restores the first seat",
      state.household is first.household and game.household is first_facade and state.acting_seat == FIRST_SEAT_ID, None)
try:
    with game.act_as("second"):
        raise RuntimeError("boom")
except RuntimeError:
    pass
check("act_as restores the seat when the body raises", state.household is first.household, None)
try:
    with game.act_as("nobody"):
        pass
    refused = False
except KeyError:
    refused = True
check("an unknown seat is refused and nothing changes", refused and state.household is first.household, None)
try:
    game.add_seat("second", SeatState(household=HouseholdState(capital=1.0), projects=ProjectsState(), founder=FounderState()))
    added_twice = True
except ValueError:
    added_twice = False
check("a seat id already taken is refused", not added_twice)

# save: the aliased root fields are not written; seats are, and a load rebinds the aliases
blob = serialize_state(state)
check("the save holds the seats and not the aliased root fields",
      "seats" in blob and "household" not in blob and "projects" not in blob and "founder" not in blob and "_goal" not in blob,
      sorted(blob))
check("the save names the acting seat", blob.get("acting_seat") == FIRST_SEAT_ID, blob.get("acting_seat"))
loaded = deserialize_state(blob)
seat = loaded.seats[FIRST_SEAT_ID]
check("a load rebinds the aliases to the loaded seat",
      loaded.household is seat.household and loaded.projects is seat.projects and loaded.founder is seat.founder, None)
check("a load restores the household and the goal",
      loaded.household.capital == 1000.0 and loaded._goal == "point_contact_transistor" and sorted(loaded.seats) == sorted(state.seats),
      (loaded.household.capital, loaded._goal))
