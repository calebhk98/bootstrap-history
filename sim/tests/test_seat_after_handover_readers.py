"""After `seat_handover` the acting seat is the replacement and the leaver is gone. Each function the year reads from the
acting seat is called on a written-out post-handover state: the replacement "heir" holds the leaver's household, known
nodes, holdings, goal and country under its own id (and its own founder); "third" is another player; "leaver" appears
nowhere. Each asserts it reads the heir's books and nothing of the leaver."""
QUICK_TOPIC = True

import json
from types import SimpleNamespace

from sim.agents.api import ActorsState
from sim.agents.household_party import HouseholdParty
from sim.engine.saveload import _get_field, acting_seat_of, goal_of_blob
from sim.knowledge.api import KnowledgeSeat
from sim.knowledge.rules import SeatTechniques
from sim.workforce.api import WorkforceSeat
from sim.seats import api as seat_builds
from sim.seats.api import (SeatsSeat, owner_of_seat, partner_country_of_seat, patron_grant_share, run_is_over, seat_ended,
                           seats_playing)
from sim.engine.state import (FounderState, HoldingsState, HouseholdState, SeatProgressState,
                              SimulationState, serialize_state)
from sim.engine.state_seat import SeatState, bind_seat
from sim.tests.harness import check
from sim.tests.seat_views_stand_in import slots_of
from sim.agents.api import Business


# what each seat chose for its inventions (the diffusion module keeps it)
DISCLOSED = {"heir": {"wheel": {"mode": "license", "licensees": {"firm:7": {"fee": 0.0, "royalty": 0.1}}}}, "third": {}}


def post_handover_state():
	"""Seats "third" and "heir", "heir" acting; the heir carries the leaver's household, nodes, holdings, goal and country."""
	heir = SeatState(
		household=HouseholdState(),
		founder=FounderState(_founder_death_year=30),
		holdings=HoldingsState(), seat_progress=SeatProgressState(),
		modules={"knowledge": KnowledgeSeat(done={"fire", "wheel"}, granted={"fire"}), "workforce": WorkforceSeat(scholars=2.0),
		         "seats": SeatsSeat(goal="steam_engine", country="han", patents={"loom": {"granted": 1, "expires": 20, "licensees": ["third"]}}, shares_held={"guild": 3.0})})
	third = SeatState(household=HouseholdState(), founder=FounderState(_founder_death_year=50),
	                  modules={"knowledge": KnowledgeSeat(done={"fire"}, granted={"fire"}), "seats": SeatsSeat(goal="printing_press")})
	state = SimulationState(seats={"third": third, "heir": heir}, acting_seat="heir", modules={"actors": ActorsState(home_country="rome")})
	state.actors.purses.set_net("heir", 40.0, "opening")      # the accounts are under the seats' ids: the leaver's money was renamed to the heir's
	state.actors.purses.set_net("third", 5.0, "opening")
	return state


def techniques_of(seats):
	"""What the knowledge module's `techniques_by_seat` view answers over these seats."""
	return {seat_id: SeatTechniques(frozenset(seat.modules["knowledge"].done), frozenset(seat.modules["knowledge"].granted))
	        for seat_id, seat in seats.items()}


def saved(state):
	return json.loads(json.dumps(serialize_state(state)))


# ---- the root aliases and the goal
state = post_handover_state()
heir = state.seats["heir"]
bind_seat(state, "heir")
check("bind_seat: the root aliases are the heir's own objects",
      state.acting_seat == "heir" and state.household is heir.household
      and state.founder is heir.founder and state.holdings is heir.holdings and state.seat_progress is heir.seat_progress
      and state.seats["heir"].modules["workforce"].scholars == 2.0 and state.founder._founder_death_year == 30, None)

# ---- the purse
state = post_handover_state()
purses = state.actors.purses
check("the purses: each seat's purse is an account under its own id and no account is the leaver's",
      purses.has_account("heir") and purses.has_account("third") and not purses.has_account("leaver"), None)
check("the purses: the acting seat's money is the heir's account", purses.net(state.acting_seat) == 40.0, purses.net(state.acting_seat))

# ---- who is still playing
state = post_handover_state()
check("seats_playing: the heir and the other player, in the order they joined", seats_playing(slots_of(state.seats)) == ["third", "heir"])
check("seat_ended: the heir's run has not ended", seat_ended(slots_of(state.seats)["heir"]) is False)
check("run_is_over: not while a seat has no goal reached", run_is_over(slots_of(state.seats)) is False)
state.seats["heir"].modules["seats"].goal_year = 120
state.seats["third"].modules["seats"].goal_year = 121
check("run_is_over: over when the heir and the other player have both reached their goals", run_is_over(slots_of(state.seats)) is True)

# ---- the country the acting seat plays for
state = post_handover_state()
check("owner_of_seat: the acting seat raises armies for the country it was handed", owner_of_seat(slots_of(state.seats), state.acting_seat, "rome") == "han")
check("owner_of_seat: the other seat plays for the game's own country", owner_of_seat(slots_of(state.seats), "third", "rome") == "rome")
check("partner_country_of_seat: the acting seat's market is its country's", partner_country_of_seat(slots_of(state.seats), state.acting_seat, "rome") == "han")
check("partner_country_of_seat: the other seat has none", partner_country_of_seat(slots_of(state.seats), "third", "rome") is None)

# ---- what the state pays the acting seat
state = post_handover_state()
grants = {"rome": 500.0, "han": 90.0}
check("patron_grant_share: the heir is paid its country's grant shared among that state's clients",
      patron_grant_share(grants.get, state.seats[state.acting_seat].modules["seats"].country, state.acting_seat, "rome", lambda country: [("heir", 0.0, 1.0), ("third", 0.0, 1.0)]) == 45.0)
check("patron_grant_share: a state that funds no heir pays it nothing",
      patron_grant_share(grants.get, state.seats[state.acting_seat].modules["seats"].country, state.acting_seat, "rome", lambda country: [("third", 0.0, 1.0)]) == 0.0)
check("patron_grant_share: the heir is asked about its own country and not the home one",
      patron_grant_share(grants.get, state.seats["heir"].modules["seats"].country, "heir", "rome", lambda country: [("heir", 0.0, 1.0)] if country == "han" else []) == 90.0)

# ---- what the seats have built
state = post_handover_state()
check("builders_of: the heir built what the leaver built and was not granted", seat_builds.builders_of(techniques_of(state.seats), "wheel") == ["heir"])
check("builders_of: a granted node has no builder", seat_builds.builders_of(techniques_of(state.seats), "fire") == [])
check("licensors_of: the heir licensed its invention to the firm", seat_builds.licensors_of(techniques_of(state.seats), "wheel", "firm:7", DISCLOSED.get) == ["heir"])
check("disclosure_modes: the heir's choice stands", seat_builds.disclosure_modes(techniques_of(state.seats), "wheel", DISCLOSED.get) == ["license"])

# ---- the seat as an actor
state = post_handover_state()
party = HouseholdParty(SimpleNamespace(_state=state), dealings=state.seats["heir"].modules["seats"], business=Business())
check("HouseholdParty: the acting seat's actor is the heir, with the heir's patents and shares",
      party.actor_id == "heir" and party.record.patents == {"loom": {"granted": 1, "expires": 20, "licensees": ["third"]}}
      and party.record.holdings == {"guild": 3.0}, party.actor_id)

# ---- the save of that state
blob = saved(post_handover_state())
check("serialize_state: the save's acting seat and its seats are the heir and the other player",
      blob["acting_seat"] == "heir" and list(blob["seats"]) == ["third", "heir"], (blob["acting_seat"], list(blob["seats"])))
check("serialize_state: the save names the leaver nowhere", "leaver" not in json.dumps(blob), None)
check("serialize_state: the heir's saved seat carries the household, nodes, goal and country passed on",
      blob["seats"]["heir"]["modules"]["workforce"]["scholars"] == 2.0 and blob["seats"]["heir"]["modules"]["knowledge"]["done"] == {"__set__": ["fire", "wheel"]}
      and blob["seats"]["heir"]["modules"]["seats"]["goal"] == "steam_engine" and blob["seats"]["heir"]["modules"]["seats"]["country"] == "han"
      and blob["seats"]["heir"]["modules"]["seats"]["shares_held"] == {"guild": 3.0}, None)
check("acting_seat_of: the save's acting seat is the heir's record", acting_seat_of(blob) is blob["seats"]["heir"])
check("goal_of_blob: the heir's goal", goal_of_blob(blob) == "steam_engine")
check("_get_field: a field of the acting seat is the heir's", _get_field(blob, "_founder_death_year") == 30 and _get_field(blob, "trades_created") is not None)
