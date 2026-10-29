"""A seat holds one player's household, projects, founder and goal; the root fields alias the acting seat. The rules are
called on a `SimulationState` and on the real `seat_registry` functions over a stub; the save and load of the seats are the state's own
serialisation."""

QUICK_TOPIC = True

from .harness import check

from sim.engine import seat_registry
from sim.engine.state import FounderState, HouseholdState, SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState


class Seats:
    """The seat switching of a game over a bare state."""

    def __init__(self, state):
        self.state = state
        self.resets = 0

    def add_seat(self, seat_id, seat):
        seat_registry.add_seat(self, seat_id, seat)

    def act_as(self, seat_id):
        return seat_registry.act_as(self, seat_id)

    def _switch_seat(self, seat_id):
        seat_registry.switch_seat(self, seat_id)

    def _reset_economic_caches(self):
        self.resets += 1


household = HouseholdState(saving_target=1000.0)
state = SimulationState(household=household, founder=FounderState())
first = state.seats[FIRST_SEAT_ID]

check("one seat exists and is acting", list(state.seats) == [FIRST_SEAT_ID] and state.acting_seat == FIRST_SEAT_ID, list(state.seats))
check("the root household and founder are the acting seat's objects",
      state.household is first.household and state.founder is first.founder, None)

# a second seat: switching rebinds the aliases, and restores on exit and on error
game = Seats(state)
second_household = HouseholdState(saving_target=50.0)
game.add_seat("second", SeatState(household=second_household, founder=FounderState()))
with game.act_as("second"):
    check("inside act_as the root household is the second seat's",
          state.household is second_household and state.household.saving_target == 50.0, state.household.saving_target)
check("leaving act_as restores the first seat",
      state.household is first.household and state.acting_seat == FIRST_SEAT_ID, None)
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
    game.add_seat("second", SeatState(household=HouseholdState(saving_target=1.0), founder=FounderState()))
    added_twice = True
except ValueError:
    added_twice = False
check("a seat id already taken is refused", not added_twice)

# save: the aliased root fields are not written; seats are, and a load rebinds the aliases
blob = serialize_state(state)
check("the save holds the seats and not the aliased root fields",
      "seats" in blob and "household" not in blob and "founder" not in blob,
      sorted(blob))
check("the save names the acting seat", blob.get("acting_seat") == FIRST_SEAT_ID, blob.get("acting_seat"))
loaded = deserialize_state(blob)
seat = loaded.seats[FIRST_SEAT_ID]
check("a load rebinds the aliases to the loaded seat",
      loaded.household is seat.household and loaded.founder is seat.founder, None)
check("a load restores the household and the seats",
      loaded.household.saving_target == 1000.0 and sorted(loaded.seats) == sorted(state.seats), loaded.household.saving_target)
