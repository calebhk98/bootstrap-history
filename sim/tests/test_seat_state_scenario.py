"""Scenarios for the seat state in a whole Rome game: the household facade and the aliases survive a save and a load.
The rules are in test_seat_state."""
import json
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.engine.state_seat import FIRST_SEAT_ID

# save: the aliased root fields are not written; seats are, and a load rebinds the aliases
other = sim(civ="rome_100ad", capital=1000.0)
other.goal = "point_contact_transistor"
saved_capital = other.household.capital
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
          other.household.capital == saved_capital and other.goal == "point_contact_transistor" and other.state.household is other.household._state.household, other.household.capital)
