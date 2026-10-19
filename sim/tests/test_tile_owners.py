"""Complaint 483: an owner map (tile -> owner and control level) seeded from the civilisation files, read by
`tiles_held`, `country_of` and the ways record, changed only by one transfer, with one owner per tile."""
import glob
import json
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.economy.api import EconomySetup
from sim.engine import invariants
from sim.engine.saveload import load_state, save_state
from sim.geography.api import tile_owners, tiles_held

# ---- seeded owners match the civilisation files -------------------------------------------------------------
for path in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "*_*.json"))):
    civ = json.load(open(path))
    if "id" not in civ:
        continue
    seeded, conflicts = tile_owners.seed({civ["id"]: tiles_held(civ)})
    check("%s: the seeded owners give back the tiles its file lists" % civ["id"],
          tiles_held(civ, owners=seeded) == tiles_held(civ) and not conflicts)

# ---- a double claim is caught ----------------------------------------------------------------------------------
seeded, conflicts = tile_owners.seed({"alpha": ["t1", "t2"], "beta": ["t2", "t3"]})
check("the first claimant keeps a tile two files claim and the second is reported",
      tile_owners.owner_of(seeded, "t2") == "alpha" and conflicts == [{"tile": "t2", "owner": "alpha", "claimant": "beta"}],
      (seeded, conflicts))
check("a tile listed by two actors is a problem",
      [found["cause"] for found in tile_owners.problems(seeded, {"alpha": ["t2"], "beta": ["t2"]})]
      == ["double_claim", "owned_by_other"])
try:
    tile_owners.transfer(seeded, "t1", "beta", "not_a_level")
    refused = False
except tile_owners.TileOwnerError:
    refused = True
check("a control level that the data does not list is refused", refused)
check("the control levels are data", {"core", "tributary", "enclave", "claimed", "ungoverned"} <= set(tile_owners.control_levels()))

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

# ---- the invariant -------------------------------------------------------------------------------------------------
check("the invariant holds on a fresh game", invariants.check_tile_owner_invariants(game))
colony = {"tile": held[1], "founded_year": 0, "by": "x", "children": 0.0, "working_age": 1.0, "elderly": 0.0}
game.state.holdings.colonies.append(dict(colony))
try:
    invariants.check_tile_owner_invariants(game)
    caught = False
except AssertionError:
    caught = True
check("the invariant fails when a colony stands on a tile another actor owns", caught)
game.transfer_tile(held[1], game.state.acting_seat, "claimed")
check("the invariant holds when the colony's seat owns its tile", invariants.check_tile_owner_invariants(game))
game.state.seats["other"] = SimpleNamespace(holdings=SimpleNamespace(colonies=[dict(colony)]))
try:
    invariants.check_tile_owner_invariants(game)
    caught = False
except AssertionError:
    caught = True
del game.state.seats["other"]
check("the invariant fails when two seats' colonies stand on one tile", caught)
game.state.holdings.colonies.clear()

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
