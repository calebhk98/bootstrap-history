"""SCENARIO (Complaint 483): the owner map in a real game: seeded from the civilisation file, moved by `transfer_tile`, read
for ways, round-tripped through save and load, and used by colonies. The rules are in test_tile_owners."""
import json  # noqa: F401
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.economy.api import EconomySetup
from sim.engine.saveload import load_state, save_state
from sim.geography.api import tile_owners, tiles_held

# ---- transfer ----------------------------------------------------------------------------------------------------
game = unopened_sim()
home = game.civ["id"]
held = game.home_tiles_held()
check("the game's seeded owners match the civilisation file's tiles", held == tiles_held(game.civ) and bool(held)
      and all(game.tile_control(tile) == tile_owners.seed_level() for tile in held))
tile = held[0]
setup = SimpleNamespace(tile_owners=game.tile_owner_map(), tiles={}, civ_id=home)
check("country_of reads the owner map", EconomySetup.country_of(setup, tile) == home)
previous = game.transfer_tile(tile, "rival", "garrisoned")
check("a transfer moves the tile, keeps one owner and sets the level",
      previous == home and game.tile_owner(tile) == "rival" and game.tile_control(tile) == "garrisoned"
      and tile not in game.home_tiles_held() and game.tiles_owned_by("rival") == [tile])
check("country_of follows the transfer", EconomySetup.country_of(setup, tile) == "rival")
check("built ways take their owner from the tiles they stand on",
      tile_owners.way_owner(game.tile_owner_map(), tile) == "rival"
      and tile_owners.way_owner(game.tile_owner_map(), "%s|%s" % (tile, held[1])) is None
      and tile_owners.way_owner(game.tile_owner_map(), "%s|%s" % (held[1], held[2])) == home)
game.state.economy.improvements["%s|%s" % (held[1], held[2])] = {"road": True}
check("the game reports a way's owner", game.way_owners() == {"%s|%s" % (held[1], held[2]): home})

# ---- save round-trip ------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = unopened_sim()
    load_state(revived, path)
check("owners and control levels round-trip through save and load",
      revived.state.economy.tile_owners == game.state.economy.tile_owners
      and revived.tile_owner(tile) == "rival" and revived.tile_control(tile) == "garrisoned")

# ---- colonies use the transfer ---------------------------------------------------------------------------------------
settler = unopened_sim(capital=1.0e12)
settler.done.update(NODES["ben_settlement_charter"]["pre"])
settler.done.add("ben_settlement_charter")
settler._done_changed()
settler.spending_power = lambda kind: settler.state.household.capital
target = settler.settlement_candidates(False)[0]
ok, text = settler.found_colony(target)
check("a founded colony's tile is owned by the founding seat at the settlement level",
      ok and settler.tile_owner(target) == settler.state.acting_seat
      and settler.tile_control(target) == tile_owners.settlement_level() and target in settler.claimed_tiles(), text)
check("a second claim on that tile is refused", not settler.found_colony(target)[0])
settler.state.holdings.colonies[0].update(children=0.0, working_age=0.0, elderly=0.0)
settler.advance_colonies(settler.state.scenario.year)
check("a colony that dies out releases its tile", settler.tile_owner(target) is None)
