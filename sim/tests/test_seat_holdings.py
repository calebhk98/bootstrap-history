"""Holder-owned economy and scenario state lives on the seat; the world parts stay on the root."""
import dataclasses
import json

from .harness import *  # noqa: F401,F403
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.state import (EconomyState, FounderState, HouseholdState, ProjectsState,
                              SimulationState, deserialize_state, serialize_state)
from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState, bind_seat
from sim.scenario.state import ScenarioWorld

QUICK_TOPIC = True

state = HouseholdPort().fresh_state(100.0)
first = state.seats[FIRST_SEAT_ID]

check("the root holdings and seat progress are the acting seat's objects",
      state.holdings is first.holdings
      and state.seat_progress is first.seat_progress, None)

state.holdings._dashboard_history = [12.0]
state.seat_progress.dashboard_history_years = 150
state.economy.nodes_money_per_labour_hour = 1.0

second = SeatState(household=HouseholdState(capital=5.0), projects=ProjectsState(), founder=FounderState())
state.seats["second"] = second
bind_seat(state, "second")
check("a second seat starts with empty holdings and progress",
      state.holdings._dashboard_history is None
      and state.seat_progress.dashboard_history_years is None, None)
check("the world economy is the same object for both seats", state.economy.nodes_money_per_labour_hour is not None, None)
state.holdings._dashboard_history = [3.0]
bind_seat(state, FIRST_SEAT_ID)
check("the first seat's holdings are untouched by the second's",
      state.holdings._dashboard_history == [12.0] and state.seat_progress.dashboard_history_years == 150, None)

blob = json.loads(json.dumps(serialize_state(state)))
check("the save holds holdings and progress inside each seat and not at the root",
      all(name in blob["seats"]["second"] for name in ("holdings", "seat_progress"))
      and not any(name in blob for name in ("holdings", "seat_progress")), sorted(blob))
check("the world economy section no longer carries holder-owned fields",
      "_dashboard_history" not in blob["economy"] and "colonies" not in blob["economy"] and "nodes_money_per_labour_hour" in blob["economy"],
      sorted(blob["economy"]))
loaded = deserialize_state(blob, SimulationState)
check("a round trip keeps each seat's own holdings",
      loaded.seats[FIRST_SEAT_ID].holdings._dashboard_history == [12.0] and loaded.seats["second"].holdings._dashboard_history == [3.0]
      and loaded.seats["second"].seat_progress.dashboard_history_years is None,
      None)
check("a load binds the root holdings to the acting seat",
      loaded.holdings is loaded.seats[FIRST_SEAT_ID].holdings, None)

# the world parts declare none of the seat's fields
world_economy = {f.name for f in dataclasses.fields(EconomyState)}
world_scenario = {f.name for f in dataclasses.fields(ScenarioWorld)}
seat_economy = {f.name for f in dataclasses.fields(HoldingsState)}
seat_scenario = {f.name for f in dataclasses.fields(SeatProgressState)}
check("the world economy declares none of the holder-owned fields",
      not (seat_economy & world_economy), sorted(seat_economy & world_economy))
check("the world scenario declares none of the seat's progress fields",
      not (seat_scenario & world_scenario), sorted(seat_scenario & world_scenario))

# a save whose seat lacks one of the seat sections is refused by name
from sim.engine.saveload import _check_save_shape
blob["_civ"] = "rome_100ad"
check("a save with every seat section passes the shape check", _check_save_shape(blob) is None, _check_save_shape(blob))
for section in ("holdings", "seat_progress"):
    broken = json.loads(json.dumps(blob))
    del broken["seats"][FIRST_SEAT_ID][section]
    message = _check_save_shape(broken)
    check("a save without the seat's %s is refused" % section, message is not None and section in message, message)
