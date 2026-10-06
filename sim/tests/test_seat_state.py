"""A seat holds one player's household, projects, founder and goal; the root fields alias the acting seat."""
import json
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.engine.state import FounderState, HouseholdState, ProjectsState
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState

game = sim(civ="rome_100ad", capital=1000.0)
first = game.state.seats[FIRST_SEAT_ID]

check("one seat exists and is acting", list(game.state.seats) == [FIRST_SEAT_ID] and game.state.acting_seat == FIRST_SEAT_ID,
      list(game.state.seats))
check("the root household, projects and founder are the acting seat's objects",
      game.state.household is first.household and game.state.projects is first.projects
      and game.state.founder is first.founder, None)
game.goal = "point_contact_transistor"
check("the root goal is the acting seat's goal", game.goal == "point_contact_transistor" and first.goal == "point_contact_transistor", first.goal)

# a second seat: switching rebinds the aliases and the facade, and restores on exit and on error
second_household = HouseholdState(capital=50.0)
game.add_seat("second", SeatState(household=second_household, projects=ProjectsState(), founder=FounderState()))
first_facade = game.household
with game.act_as("second"):
    check("inside act_as the root household is the second seat's",
          game.state.household is second_household and game.household.capital == 50.0, game.household.capital)
    check("each seat has its own household facade", game.household is not first_facade, None)
    check("the second seat has no goal of its own", game.goal is None, game.goal)
check("leaving act_as restores the first seat",
      game.state.household is first.household and game.household is first_facade and game.state.acting_seat == FIRST_SEAT_ID, None)
try:
    with game.act_as("second"):
        raise RuntimeError("boom")
except RuntimeError:
    pass
check("act_as restores the seat when the body raises", game.state.household is first.household, None)
try:
    with game.act_as("nobody"):
        pass
    refused = False
except KeyError:
    refused = True
check("an unknown seat is refused and nothing changes", refused and game.state.household is first.household, None)

# save: the aliased root fields are not written; seats are, and a load rebinds the aliases
other = sim(civ="rome_100ad", capital=1000.0)
other.goal = "point_contact_transistor"
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(other, path)
    with open(path) as handle:
        blob = json.load(handle)
    check("the save holds the seats and not the aliased root fields",
          "seats" in blob and "household" not in blob and "projects" not in blob and "founder" not in blob and "_goal" not in blob,
          sorted(blob))
    check("the save names the acting seat", blob.get("acting_seat") == FIRST_SEAT_ID, blob.get("acting_seat"))
    other.household.capital = 7.0
    load_state(other, path)
    seat = other.state.seats[FIRST_SEAT_ID]
    check("a load rebinds the aliases to the loaded seat",
          other.state.household is seat.household and other.state.projects is seat.projects and other.state.founder is seat.founder, None)
    check("a load restores the household, goal and facade",
          other.household.capital == 1000.0 and other.goal == "point_contact_transistor" and other.state.household is other.household._state.household, other.household.capital)
