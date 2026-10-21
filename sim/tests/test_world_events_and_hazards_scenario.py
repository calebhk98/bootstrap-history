"""Scenarios (Complaint 493 and 640): in a built game of Rome and Han a certain hazard hits both countries, a transfer is
written to the world event log a second seat reads through the protocol, the log round-trips through a save, and the yearly
check fails on a forced violation. The hazard, transfer, famine and invariant rules are called on stand-in games in
test_world_hazard_rules; the log's bound, the draw and when the yearly checks run are in test_world_events_and_hazards."""
import os
import random
import tempfile
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.agents.api import seed_strata
from sim.engine.agents_port import SimWorld
from sim.engine.agents_port_cast import seed_opening_cast
from sim.agents.api import cast_from_civilisations, seed_cast
from sim.engine import invariants, world_events, world_hazard_data, world_hazards
from sim.engine.saveload import load_state, save_state

PARTNER = "han_china_100ad"


def two_country_game():
    """A game of Rome and Han, with the roster seeded ."""
    civ = S.load_civ("rome_100ad")
    game = build_unopened(lambda: S.Sim(NODES, list(ORDER), random.Random(1), events=True, manual=True, civ=civ))
    game.partner_countries = lambda: [PARTNER]
    game.partners_in_agent_economy = lambda: [PARTNER]
    game.goal, game.done_year = GOAL, {}
    seed_opening_cast(game)
    # the harness leaves out a partner the agent economy holds, and the opening cast is then home alone: seed the partner's
    home_country, entries, profiles = cast_from_civilisations(game.start_civ, [S.load_civ(PARTNER)])
    seed_cast(game.actors, home_country, entries, profiles)
    seed_strata(game.actors, SimWorld(game))
    return game


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


def fails(check_function, target):
    try:
        check_function(target)
        return False
    except AssertionError:
        return True


game = two_country_game()
year = game.state.scenario.year
check("the game has two countries", world_hazards.countries_in_game(game) == ["rome_100ad", PARTNER])
partner_people = world_hazards.people_of(game, PARTNER)
check("the partner has people in its strata", partner_people > 0.0, partner_people)

# ---- a world hazard can hit a partner country --------------------------------------------------------------
flood = next(entry for entry in world_hazard_data.hazards() if entry["kind"] == "flood")
with mock.patch.object(world_hazard_data, "hazards", lambda: [dict(flood, annual_chance=1.0)]):
    world_hazards.world_hazards_phase(game, game.playing_seats())
hits = world_events.rows(game, "flood")
check("a certain flood hits both countries and writes one record each",
      sorted(row["actors"][0] for row in hits) == sorted(["rome_100ad", PARTNER]), hits)
check("the record carries a year, a cause and structured facts",
      all(row["year"] == year and row["cause"] == flood["cause"] and row["facts"]["population_loss"] > 0 for row in hits))

# ---- a transfer writes a dated event a second seat can read ----------------------------------------------------------
tile = game.tiles_owned_by("rome_100ad")[0]
game.transfer_tile(tile, PARTNER, "garrisoned", cause="conquest")
game.join_seat("second", {"start_capital": 1.0e6})
with game.act_as("second"):
    answer = ask(game, cmd="world_events", id="tile_transfer")
transfers = answer["events"]
check("a second seat reads the transfer with year, actors, tile, cause and facts",
      answer["ok"] and len(transfers) == 1 and transfers[0]["year"] == game.state.scenario.year
      and transfers[0]["tiles"] == [tile] and transfers[0]["cause"] == "conquest"
      and transfers[0]["actors"] == ["rome_100ad", PARTNER]
      and transfers[0]["facts"]["to_owner"] == PARTNER and transfers[0]["facts"]["control"] == "garrisoned", answer)

# ---- the log round-trips through save and load -----------------------------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = two_country_game()
    load_state(revived, path)
check("the world event log round-trips", revived.state.economy.world_events == game.state.economy.world_events
      and len(revived.state.economy.world_events) >= 3)

# ---- each yearly check fails on a forced violation ---------------------------------------------------------------------
check("the yearly checks hold on a fresh game", invariants.check_yearly_invariants(two_country_game()))

tile_game = two_country_game()
owners = tile_game.tile_owner_map()
tile_game.stores.view("control").set(next(iter(owners)), "no_such_level")
check("the ownership check fails on an unknown control level", fails(invariants.check_yearly_invariants, tile_game))
