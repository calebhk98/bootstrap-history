"""After `seat_handover` the acting seat is the replacement and the leaver is gone. Each function the year reads from the
acting seat is called on a written-out post-handover state: the replacement "heir" holds the leaver's household, known
nodes, holdings, goal and country under its own id (and its own founder); "third" is another player; "leaver" appears
nowhere. Each asserts it reads the heir's books and nothing of the leaver."""
QUICK_TOPIC = True

import json
from types import SimpleNamespace

from sim.agents.api import ActorsState
from sim.agents.household_party import HouseholdParty
from sim.engine import seat_builds
from sim.engine.saveload import _get_field, acting_seat_of, goal_of_blob
from sim.engine.seat_country import owner_of_seat, partner_country_of_seat, patron_grant_share
from sim.engine.seat_run import run_is_over, seat_ended, seats_playing
from sim.engine.state import (FounderState, HoldingsState, HouseholdState, ProjectsState, SeatProgressState,
                              SimulationState, serialize_state)
from sim.engine.state_seat import SeatState, bind_seat
from sim.tests.harness import check


def post_handover_state():
	"""Seats "third" and "heir", "heir" acting; the heir carries the leaver's household, nodes, holdings, goal and country."""
	heir = SeatState(
		household=HouseholdState(capital=40.0, scholars=2.0, reputation=7.0),
		projects=ProjectsState(done={"fire", "wheel"}, granted={"fire"}),
		founder=FounderState(life_left=30.0),
		holdings=HoldingsState(patents={"loom": {"granted": 1, "expires": 20, "licensees": ["third"]}}, shares_held={"guild": 3.0}),
		seat_progress=SeatProgressState(goal_year=None),
		goal="steam_engine", country="han")
	heir.projects.disclosures["wheel"] = {"mode": "license", "licensees": {"firm:7": {"fee": 0.0, "royalty": 0.1}}}
	third = SeatState(household=HouseholdState(capital=5.0), projects=ProjectsState(done={"fire"}, granted={"fire"}),
	                  founder=FounderState(life_left=50.0), goal="printing_press")
	return SimulationState(seats={"third": third, "heir": heir}, acting_seat="heir", actors=ActorsState(home_country="rome"))


def saved(state):
	return json.loads(json.dumps(serialize_state(state)))


# ---- the root aliases and the goal
state = post_handover_state()
heir = state.seats["heir"]
bind_seat(state, "heir")
check("bind_seat: the root aliases are the heir's own objects",
      state.acting_seat == "heir" and state.household is heir.household and state.projects is heir.projects
      and state.founder is heir.founder and state.holdings is heir.holdings and state.seat_progress is heir.seat_progress
      and state.household.scholars == 2.0 and state.founder.life_left == 30.0, None)
check("SimulationState._goal: reads the heir's goal", post_handover_state()._goal == "steam_engine")
state = post_handover_state()
state._goal = "radio"
check("SimulationState._goal: writes the heir's goal and not the other seat's",
      state.seats["heir"].goal == "radio" and state.seats["third"].goal == "printing_press", None)

# ---- the purse
state = post_handover_state()
purses = state.actors.purses
check("attach_purses: each seat's purse is an account under its own id and no account is the leaver's",
      state.household.account == "heir" and state.seats["third"].household.account == "third"
      and purses.has_account("heir") and purses.has_account("third") and not purses.has_account("leaver"), None)
check("attach_purses: the acting household's capital is the heir's account", state.household.capital == 40.0 and purses.net("heir") == 40.0,
      (state.household.capital, purses.net("heir")))

# ---- who is still playing
state = post_handover_state()
check("seats_playing: the heir and the other player, in the order they joined", seats_playing(state.seats) == ["third", "heir"])
check("seat_ended: the heir's run has not ended", seat_ended(state.seats["heir"]) is False)
check("run_is_over: not while a seat has no goal reached", run_is_over(state.seats) is False)
state.seats["heir"].seat_progress.goal_year = 120
state.seats["third"].seat_progress.goal_year = 121
check("run_is_over: over when the heir and the other player have both reached their goals", run_is_over(state.seats) is True)

# ---- the country the acting seat plays for
state = post_handover_state()
check("owner_of_seat: the acting seat raises armies for the country it was handed", owner_of_seat(state.seats, state.acting_seat, "rome") == "han")
check("owner_of_seat: the other seat plays for the game's own country", owner_of_seat(state.seats, "third", "rome") == "rome")
check("partner_country_of_seat: the acting seat's market is its country's", partner_country_of_seat(state.seats, state.acting_seat, "rome") == "han")
check("partner_country_of_seat: the other seat has none", partner_country_of_seat(state.seats, "third", "rome") is None)

# ---- what the state pays the acting seat
state = post_handover_state()
records = {"government:rome": SimpleNamespace(patron_grant=500.0), "government:han": SimpleNamespace(patron_grant=90.0)}
check("patron_grant_share: the heir is paid its country's grant shared among that state's clients",
      patron_grant_share(records, state.seats, state.acting_seat, "rome", lambda country: [("heir", 0.0, 1.0), ("third", 0.0, 1.0)]) == 45.0)
check("patron_grant_share: a state that funds no heir pays it nothing",
      patron_grant_share(records, state.seats, state.acting_seat, "rome", lambda country: [("third", 0.0, 1.0)]) == 0.0)
check("patron_grant_share: the heir is asked about its own country and not the home one",
      patron_grant_share(records, state.seats, "heir", "rome", lambda country: [("heir", 0.0, 1.0)] if country == "han" else []) == 90.0)

# ---- what the seats have built
state = post_handover_state()
check("builders_of: the heir built what the leaver built and was not granted", seat_builds.builders_of(state.seats, "wheel") == ["heir"])
check("builders_of: a granted node has no builder", seat_builds.builders_of(state.seats, "fire") == [])
check("licensors_of: the heir licensed its invention to the firm", seat_builds.licensors_of(state.seats, "wheel", "firm:7") == ["heir"])
check("disclosure_modes: the heir's choice stands", seat_builds.disclosure_modes(state.seats, "wheel") == ["license"])

# ---- the seat as an actor
state = post_handover_state()
party = HouseholdParty(SimpleNamespace(_state=state))
check("HouseholdParty: the acting seat's actor is the heir, with the heir's patents and shares",
      party.actor_id == "heir" and party.record.patents == {"loom": {"granted": 1, "expires": 20, "licensees": ["third"]}}
      and party.record.holdings == {"guild": 3.0}, party.actor_id)

# ---- the save of that state
blob = saved(post_handover_state())
check("serialize_state: the save's acting seat and its seats are the heir and the other player",
      blob["acting_seat"] == "heir" and list(blob["seats"]) == ["third", "heir"], (blob["acting_seat"], list(blob["seats"])))
check("serialize_state: the save names the leaver nowhere", "leaver" not in json.dumps(blob), None)
check("serialize_state: the heir's saved seat carries the household, nodes, goal and country passed on",
      blob["seats"]["heir"]["household"]["scholars"] == 2.0 and blob["seats"]["heir"]["projects"]["done"] == {"__set__": ["fire", "wheel"]}
      and blob["seats"]["heir"]["goal"] == "steam_engine" and blob["seats"]["heir"]["country"] == "han"
      and blob["seats"]["heir"]["holdings"]["shares_held"] == {"guild": 3.0}, None)
check("acting_seat_of: the save's acting seat is the heir's record", acting_seat_of(blob) is blob["seats"]["heir"])
check("goal_of_blob: the heir's goal", goal_of_blob(blob) == "steam_engine")
check("_get_field: a field of the acting seat is the heir's", _get_field(blob, "life_left") == 30.0 and _get_field(blob, "reputation") == 7.0)
