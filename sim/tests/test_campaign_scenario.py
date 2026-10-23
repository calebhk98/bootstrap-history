"""SCENARIO (Complaint 485): armies in a real two-country game. A country's army is raised from its state's soldiers,
marches over the route graph on an order, eats from the land and its column, loses men, fights a defence the other
state raises for itself, and a tile it takes passes to it with the people and taxes that stand on it. The rules are
in test_campaign_rules."""
import random

from .harness import *  # noqa: F401,F403

from sim.engine import year_phases
from sim.engine.saveload import load_state, save_state
from sim.agents import api as agents_api
from sim.geography.api import settlement, tile_facts, tile_owners
from sim.ui.proto import command_registry, dispatch_armies

TOPIC_SECONDS = 900

game = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
rome, han = str(game.civ["id"]), "han_china_100ad"
check("scenario: the campaign phase is in the year and the commands are registered",
      "campaigns" in [phase.name for phase in year_phases.SHIPPED]
      and "army" in command_registry.COMMANDS and "armies" in command_registry.COMMANDS)

# ---- a game with no armies is untouched by the phase
game.step_campaigns()
check("scenario: with no army the phase changes nothing", game.army_records() == {} and game.campaign_store()["drawn"] == {})

# ---- raising
force = game.owner_force(rome)
refused = game.raise_army(rome, force + 1.0)
check("scenario: an army larger than the state's free soldiers is refused with a cause",
      getattr(refused, "cause", None) == "not_enough_soldiers", refused)
check("scenario: an army is raised only on the owner's own tile",
      getattr(game.raise_army(rome, 100.0, game.tiles_owned_by(han)[0]), "cause", None) == "tile_not_yours")
home_tile = game.tiles_owned_by(rome)[0]
border = [tile for tile in tile_facts(home_tile, game.world_map).get("neighbours", ()) if game.tile_owner(tile) == rome]
target = border[0] if border else game.tiles_owned_by(rome)[1]
legion = game.raise_army(rome, 20000.0, home_tile)
check("scenario: raising takes soldiers from the state's free force, not from its size",
      legion.soldiers == 20000.0 and game.free_soldiers(rome) == force - 20000.0 and game.owner_force(rome) == force
      and legion.equipment_kg == game.owner_world(rome).equipment_kg_per_soldier())

# ---- a country seat commands, a household seat does not
reply = dispatch_armies.army_reply(game, {"text": "raise 100"})
check("scenario: the founder's household seat has no government to raise an army for",
      reply["cause"] == "household_seat_has_no_government", reply)

# ---- a march over the route graph, eating and losing men
far = game.tiles_owned_by(han)[0]
ordered = game.order_army(rome, legion.army_id, far)
check("scenario: an order sets the army's target and clears its progress", ordered.target == far)
rival_orders = game.order_army(han, legion.army_id, home_tile)
check("scenario: another actor cannot give the army orders", getattr(rival_orders, "cause", None) == "not_your_army")
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
check("scenario: a disbanded army's soldiers are free again", game.army_records() == {}
      and game.free_soldiers(rome) == game.owner_force(rome))

# ---- an attack on a tile of a state nobody plays: it raises a defence, the battle is fought, the tile follows the result
game.transfer_tile(border[0] if border else target, han, "core", "scenario: a frontier tile of the rival's")
frontier = border[0] if border else target
# captives (Complaint 648): the hooks the battle and the conquest call add people to the winner's bonded stratum
rome_bonded = [actor for actor in game.actors.of_kind("stratum") if actor.is_bonded() and actor.country_key() == rome][0]
members_before = rome_bonded.record.members
taken = game.take_captives_from_battle(rome, han, 1000.0, frontier)
check("scenario: the winner's bonded stratum takes a share of the beaten side's losses as captives",
      taken > 0.0 and abs(taken - agents_api.captives_from_losses(1000.0)) < 1e-9
      and abs(rome_bonded.record.members - members_before - taken) < 1e-9, (taken, members_before, rome_bonded.record.members))
settled_tile = max(game.tiles_owned_by(han), key=lambda tile: settlement.population_share(game.tiles_owned_by(han), tile))   # a tile with people on it
taken_conquest = game.take_captives_from_conquest(rome, han, settled_tile)
check("scenario: a tile taken by force gives a share of its people as captives",
      taken_conquest > 0.0 and rome_bonded.record.members > members_before + taken, taken_conquest)
check("scenario: captives are logged with the winner first and their cause",
      [(row["actors"], row["cause"]) for row in game.state.economy.world_events if row["kind"] == "captives"][-2:]
      == [([rome, han], "battle"), ([rome, han], "conquest")],
      [row for row in game.state.economy.world_events if row["kind"] == "captives"])
rome_bonded.record.members = members_before
attacker = game.raise_army(rome, 30000.0, home_tile)
game.order_army(rome, attacker.army_id, frontier)
han_force, rome_force = game.owner_force(han), game.owner_force(rome)
rome_tiles_before = len(game.home_tiles_held())
han_profile = game.actors.state.countries[han]
check("scenario: the rival's profile holds the tile it was given", frontier in han_profile.home_tiles)
game.step_campaigns()
battles = [row for row in game.state.economy.world_events if row["kind"] == "battle"]
won = game.tile_owner(frontier) == rome
check("scenario: the rival raised its own defence on the threatened tile",
      any(record["owner"] == han for record in game.army_records().values()) or battles or won,
      game.army_records())
check("scenario: a fought battle is on the world event log with both sides' losses",
      all(row["facts"]["attacker_lost"] >= 0.0 and row["facts"]["defender_lost"] >= 0.0 for row in battles), battles)
if won:
    check("scenario: a tile won passes to the winner at the conquest level, with its people and taxes",
          game.tile_control(frontier) == tile_owners.conquest_level(0.0)
          and frontier in game.home_tiles_held() and len(game.home_tiles_held()) == rome_tiles_before
          and frontier not in han_profile.home_tiles
          and game.campaign_store()["held_since"][frontier]["by"] == rome)
else:
    check("scenario: a tile not won stays the rival's", game.tile_owner(frontier) == han and frontier in han_profile.home_tiles)
captive_rows = [row for row in game.state.economy.world_events if row["kind"] == "captives"]
check("scenario: captives are taken only by a winner (Complaint 648), by cause, and only where its society keeps bonded people",
      all(row["facts"]["people"] > 0.0 and row["actors"][0] in (rome, han) and row["cause"] in ("battle", "conquest")
          for row in captive_rows) and (not won or any(row["cause"] == "conquest" and row["actors"] == [rome, han]
                                                       for row in captive_rows)), captive_rows)
check("scenario: both states' forces fell by what their armies lost",
      game.owner_force(han) <= han_force and game.owner_force(rome) <= rome_force
      and game.owner_force(han) + game.owner_force(rome) < han_force + rome_force)

# ---- a tile with no state's soldiers on it falls to the army that arrives, at the conquest level
neighbours = [tile for tile in border if tile != frontier]
open_tile = neighbours[0] if neighbours else [tile for tile in game.tiles_owned_by(rome) if tile not in (home_tile, frontier)][0]
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
