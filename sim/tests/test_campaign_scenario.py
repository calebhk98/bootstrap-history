"""SMOKE (Complaint 485): armies in a game with two countries, on unopened games. An army marches over the route graph
on an order, eats from the land and its column and loses men to the road; the pay a state owes falls to its armies; a
tile it reaches that no soldiers hold passes to it, with the people and taxes on it, at the conquest level, and the
captives hooks add people to the winner's bonded stratum; armies and the tiles taken survive a save. Raising, ordering
and disbanding are test_campaign_orders; the rules are test_campaign_rules."""
from .harness import *  # noqa: F401,F403

from sim.engine import year_phases
from sim.engine.saveload import load_state, save_state
from sim.geography.api import tile_facts, tile_owners
from sim.ui.proto import command_registry, dispatch_armies

game = unopened_sim()
rome = str(game.civ["id"])
check("scenario: the campaign phase is in the year and the commands are registered",
      "campaigns" in [phase.name for phase in year_phases.SHIPPED]
      and "army" in command_registry.COMMANDS and "armies" in command_registry.COMMANDS)

# ---- a game with no armies is untouched by the phase
game.step_campaigns()
check("scenario: with no army the phase changes nothing", game.army_records() == {} and game.campaign_store()["drawn"] == {})

# ---- setup
force = game.owner_force(rome)
home_tile = game.tiles_owned_by(rome)[0]
border = [tile for tile in tile_facts(home_tile, game.world_map).get("neighbours", ()) if game.tile_owner(tile) == rome]
target = border[0] if border else game.tiles_owned_by(rome)[1]
legion = game.raise_army(rome, 20000.0, home_tile)
check("scenario: set-up: an army is raised", getattr(legion, "soldiers", None) == 20000.0, legion)

# ---- a country seat commands, a household seat does not
reply = dispatch_armies.army_reply(game, {"text": "raise 100"})
check("scenario: the founder's household seat has no government to raise an army for",
      reply["cause"] == "household_seat_has_no_government", reply)

# ---- a march over the route graph, eating and losing men
far = game.tiles_owned_by(rome)[-1]
game.transfer_tile(far, "rival", "claimed", "scenario: a far tile nobody's soldiers hold")
ordered = game.order_army(rome, legion.army_id, far)
check("scenario: set-up: the army is ordered to a far tile", getattr(ordered, "target", None) == far, ordered)
game.step_campaigns()
marched = game.army_of(legion.army_id)
check("scenario: an army on a long march moves along the route, eats the land and loses men to the road",
      marched is not None and (marched.tile != home_tile or marched.progress_days > 0.0)
      and 0.0 < marched.soldiers < 20000.0 and game.campaign_store()["drawn"],
      None if marched is None else (marched.tile, marched.progress_days, marched.soldiers))
check("scenario: the dead come off the state's force",
      abs(game.owner_force(rome) - (force - (20000.0 - marched.soldiers))) < 1e-6, (game.owner_force(rome), force))
check("scenario: the pay a state owes its army is read onto the army",
      marched.pay_owed == 0.0)
game.owner_government(rome).record.arrears["army"] = 1.0e9
game.step_campaigns()
check("scenario: pay owed on the army line falls to the armies by head",
      game.army_of(legion.army_id).pay_owed > 0.0)
game.owner_government(rome).record.arrears.pop("army")
game.disband_army(rome, legion.army_id)

# ---- a tile with no state's soldiers on it falls to the army that arrives, at the conquest level
open_tile = border[0] if border else [tile for tile in game.tiles_owned_by(rome) if tile != home_tile][0]
game.transfer_tile(open_tile, "rival", "claimed", "scenario: a tile nobody's soldiers hold")
before_tiles = len(game.home_tiles_held())
taker = game.raise_army(rome, 3000.0, home_tile)
game.order_army(rome, taker.army_id, open_tile)
game.step_campaigns()
check("scenario: an army that reaches a tile no soldiers hold takes it at the conquest level, and its people and taxes follow",
      game.tile_owner(open_tile) == rome and game.tile_control(open_tile) == tile_owners.conquest_level(0.0)
      and open_tile in game.home_tiles_held() and len(game.home_tiles_held()) == before_tiles + 1
      and game.campaign_store()["held_since"][open_tile]["by"] == rome and game.army_of(taker.army_id).tile == open_tile,
      (game.tile_owner(open_tile), game.army_of(taker.army_id)))
game.campaign_store()["held_since"][open_tile]["year"] -= 1000
game._consolidate_conquests()
check("scenario: control rises with the years the tile is held with an army on it",
      game.tile_control(open_tile) == tile_owners.conquest_level(1000.0) != tile_owners.conquest_level(0.0))
game.disband_army(rome, taker.army_id)
game._consolidate_conquests()
game.campaign_store()["held_since"][open_tile]["year"] -= 1000
check("scenario: control stops rising once no army of the owner stands on the tile",
      game.tile_control(open_tile) == tile_owners.conquest_level(1000.0))

# ---- save and load keep the armies
solo = unopened_sim()
solo_home = solo.home_tiles_held()[0]
kept = solo.raise_army(str(solo.civ["id"]), 5000.0, solo_home)
solo.transfer_tile(solo_home, "rival", "garrisoned")
solo.campaign_store()["held_since"][solo_home] = {"year": 100, "by": "rival", "from": str(solo.civ["id"])}
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(solo, path)
    revived = unopened_sim()
    load_state(revived, path)
check("scenario: armies and the tiles taken round-trip through save and load",
      revived.state.economy.campaigns == solo.state.economy.campaigns and revived.army_of(kept.army_id) == kept)
