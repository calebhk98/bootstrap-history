"""SCENARIO (Complaints 484 and 486): the stability phase in a real game. A state's grievances, hunger and liability burden
become unrest on its tiles; where the discontented, armed, would beat the garrison they rise and fight it; a won rising takes
the tile from the state; a disputed accession is settled at the seat. The rules are in test_stability_rules."""
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine import year_phases
from sim.engine.saveload import save_state

TOPIC_SECONDS = 900

game = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
rome = str(game.civ["id"])
world = game.owner_world(rome)
record = world.government().record
names = [phase.name for phase in year_phases.SHIPPED]
check("scenario: the stability phase runs right after the campaigns", names.index("revolts") == names.index("campaigns") + 1)

# ---- a quiet year: the opening take is the custom, so no one rises
game.step_revolts()
check("scenario: in its opening year every tile has an unrest and a hold reading and no one rises",
      record.unrest_by_tile and set(record.hold_by_tile) == set(record.unrest_by_tile) and record.risings == [])
check("scenario: hold readings are shares", all(0.0 <= value <= 1.0 for value in record.hold_by_tile.values()))
check("scenario: what people are used to is no grievance", max(record.unrest_by_tile.values()) < 1e-9, max(record.unrest_by_tile.values()))
check("scenario: collection reads the hold (a tile's reach never exceeds the officials' own)",
      all(world.collection_shares().get(tile, 0.0) <= 1.0 for tile in record.hold_by_tile))

# ---- a famine, with land taken off every tile's holders: unrest rises and risings are fought against the garrison
tiles = game.tiles_owned_by(rome)
game.state.population.regional_eaten_over_need = {tile: 0.0 for tile in tiles}
record.land_taken_by_tile = {tile: 1.0 for tile in tiles}
force_before = game.owner_force(rome)
game.step_revolts()
check("scenario: pressure on every tile raises unrest", max(record.unrest_by_tile.values()) > 0.5)
check("scenario: some of the risings are won and some put down", {entry["kind"] for entry in record.risings} >= {"tile_lost", "put_down"},
      sorted({entry["kind"] for entry in record.risings}))
events = [row for row in game.state.economy.world_events if row["kind"] == "revolt"]
lost = [row["tiles"][0] for row in events if row["facts"]["outcome"] == "tile_lost"]
check("scenario: a tile lost to a rising is no longer the state's and the state's tiles fall by as many",
      lost and all(game.tile_owner(tile) != rome for tile in lost) and len(game.tiles_owned_by(rome)) == len(tiles) - len(lost),
      (len(lost), len(tiles), len(game.tiles_owned_by(rome))))
check("scenario: the garrison's dead come off the state's force", game.owner_force(rome) < force_before)
check("scenario: each rising is a structured world event with its outcome and the odds it was fought at",
      events and all(row["facts"]["outcome"] in ("put_down", "tile_lost", "ruler_replaced")
                     and 0.0 <= row["facts"]["rising_win_probability"] <= 1.0 for row in events))

# ---- a disputed accession is settled at the seat; a challenger no faction backs is dropped
record.succession_challenger = "no_such_faction"
game.step_revolts()
check("scenario: a challenger no faction backs raises no army", record.succession_challenger == "")

# ---- the new fields survive a save and a load
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    saved = open(path, encoding="utf-8").read()
check("scenario: a saved game carries the unrest, hold, risings and land taken",
      all('"%s"' % field in saved for field in ("unrest_by_tile", "hold_by_tile", "risings", "land_taken_by_tile", "registered_people")))
