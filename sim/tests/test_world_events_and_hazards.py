"""Complaint 493: base-rate world hazards hit every country, a dated world event log is saved and readable by every
seat, and the yearly checks (ownership, technique, capacity) run in a game of several countries."""
import os
import random
import tempfile
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.agents.business_plant import Plant
from sim.agents.api import seed_strata
from sim.engine.agents_port import SimWorld
from sim.engine.agents_port_cast import seed_opening_cast
from sim.agents.api import cast_from_civilisations, seed_cast
from sim.engine import invariants, world_events, world_hazard_data, world_hazards, year_run
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
partner_hit = next(row for row in hits if row["actors"] == [PARTNER])
check("the partner's people fall by the hazard's share",
      abs(world_hazards.people_of(game, PARTNER) - partner_people * (1 - flood["population_loss"])) < 1e-6
      and abs(partner_hit["facts"]["died"] - partner_people * flood["population_loss"]) < 1e-6, partner_hit)
check("the record carries a year, a cause and structured facts",
      partner_hit["year"] == year and partner_hit["cause"] == flood["cause"] and partner_hit["facts"]["population_loss"] > 0)
before = len(game.state.economy.world_events)
with mock.patch.object(world_hazard_data, "hazards", lambda: [dict(flood, annual_chance=0.0)]):
    world_hazards.world_hazards_phase(game, game.playing_seats())
check("a zero chance hits no one", len(game.state.economy.world_events) == before)

# ---- the draw belongs to the country and the year, not to shared dice ----------------------------------------------
check("a country's draw is the same on every call and differs between countries",
      world_hazards.draw(game, PARTNER, "flood", year) == world_hazards.draw(game, PARTNER, "flood", year)
      != world_hazards.draw(game, "rome_100ad", "flood", year))

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

# ---- famine abroad ---------------------------------------------------------------------------------------------------
for stratum in game.actors.of_kind("stratum"):
    if stratum.record.country == PARTNER:
        stratum.record.shortfall["food"] = 0.5
world_hazards.famine_watch_phase(game, game.playing_seats())
famine = world_events.rows(game, "famine", actor=PARTNER)
check("a country whose food is short has a famine record", len(famine) == 1 and famine[0]["facts"]["food_shortfall"] >= 0.5, famine)
check("a country with food has none", not world_events.rows(game, "famine", actor="rome_100ad"))

# ---- the log round-trips through save and load -----------------------------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = two_country_game()
    load_state(revived, path)
check("the world event log round-trips", revived.state.economy.world_events == game.state.economy.world_events
      and len(revived.state.economy.world_events) >= 4)

# ---- the log keeps a bounded number of years ---------------------------------------------------------------------------
old = two_country_game()
world_events.record(old, "flood", actors=["x"])
old.state.scenario.year += world_hazard_data.years_kept() + 1
world_events.record(old, "flood", actors=["y"])
check("records older than the kept years are dropped", [row["actors"] for row in old.state.economy.world_events] == [["y"]])

# ---- each yearly check fails on a forced violation ---------------------------------------------------------------------
check("the yearly checks hold on a fresh game", invariants.check_yearly_invariants(two_country_game()))

tile_game = two_country_game()
owners = tile_game.tile_owner_map()
tile_game.stores.view("control").set(next(iter(owners)), "no_such_level")
check("the ownership check fails on an unknown control level", fails(invariants.check_yearly_invariants, tile_game))

technique_game = two_country_game()
holder = technique_game.actors.of_kind("church")[0]
holder.record.business.plants.append(Plant(entry_key="no_such_technique"))
holder.record.business.__post_init__()
check("the technique check fails when an actor runs a plant it does not hold",
      fails(invariants.check_technique_invariants, technique_game))

capacity_game = two_country_game()
capacity_game.actors.of_kind("church")[0].record.workforce["any_trade"] = 1.0e15
check("the capacity check fails when an actor employs more people than the country has",
      fails(invariants.check_capacity_invariants, capacity_game))

# ---- the yearly check runs without sim.debug in a game of several countries --------------------------------------------
ran = []
runner = two_country_game()
runner.debug = False
with mock.patch.object(invariants, "check_yearly_invariants", lambda target: ran.append(target) or True), \
        mock.patch.object(year_run, "run_phases", lambda target: None):
    year_run.run_year(runner)
check("a year in a multi-country game runs the yearly checks with debug off", ran == [runner])
single = unopened_sim()
single.debug = False
ran.clear()
with mock.patch.object(invariants, "check_yearly_invariants", lambda target: ran.append(target) or True), \
        mock.patch.object(year_run, "run_phases", lambda target: None):
    year_run.run_year(single)
check("a single-country game does not pay for them", not ran, single.partners_in_agent_economy())
