"""A seat holds one player's household, projects, founder and goal; `acting_record` is the acting seat's. The rules are
called on a `SimulationState` and on `seat_registry.add_seat` over a stub; the save and load of the seats are the state's own
serialisation."""

QUICK_TOPIC = True

from .harness import check

from sim.engine import seat_registry
from sim.engine.state import FounderState, HouseholdState, SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState


class Seats:
    """The seat registry of a game over a bare state."""

    def __init__(self, state):
        self.state = state

    def add_seat(self, seat_id, seat):
        seat_registry.add_seat(self, seat_id, seat)


household = HouseholdState(saving_target=1000.0)
state = SimulationState(household=household, founder=FounderState())
first = state.seats[FIRST_SEAT_ID]

check("one seat exists and is acting", list(state.seats) == [FIRST_SEAT_ID] and state.acting_seat == FIRST_SEAT_ID, list(state.seats))
check("the root household and founder are the acting seat's objects",
      state.acting_record.household is first.household and state.acting_record.founder is first.founder, None)

# a second seat joins the registry after the first; the assembly's act_as (test_assembly_seating) names which one acts
game = Seats(state)
second_household = HouseholdState(saving_target=50.0)
game.add_seat("second", SeatState(household=second_household, founder=FounderState()))
check("a second seat joins after the first", list(state.seats) == [FIRST_SEAT_ID, "second"], list(state.seats))
try:
    game.add_seat("second", SeatState(household=HouseholdState(saving_target=1.0), founder=FounderState()))
    added_twice = True
except ValueError:
    added_twice = False
check("a seat id already taken is refused", not added_twice)

# save: the seats are written, not the build-time household and founder
blob = serialize_state(state)
check("the save holds the seats and not the build-time root fields",
      "seats" in blob and "household" not in blob and "founder" not in blob,
      sorted(blob))
check("the save names the acting seat", blob.get("acting_seat") == FIRST_SEAT_ID, blob.get("acting_seat"))
loaded = deserialize_state(blob)
seat = loaded.seats[FIRST_SEAT_ID]
check("a load names the loaded seat the acting one",
      loaded.acting_record.household is seat.household and loaded.acting_record.founder is seat.founder, None)
check("a load restores the household and the seats",
      loaded.acting_record.household.saving_target == 1000.0 and sorted(loaded.seats) == sorted(state.seats), loaded.acting_record.household.saving_target)
