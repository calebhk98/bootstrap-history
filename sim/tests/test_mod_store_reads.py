"""How a mod's declared store reaches the player and the base game (Complaint 495): a read command shows a store's value by its dotted
state path, the map shows a tile store as a layer, and tile control is the base game's `control` store. Each is called on a stand-in game holding only what it reads; the declaration rules are test_mod_stores.
Store values live in the stores module's saved state, which the save walks like any other state."""
from types import SimpleNamespace
from unittest import mock

from sim.content import api as content
from sim.stores.api import StoreSpec
from sim.ui.proto import mod_commands, screen_map

from .harness import *  # noqa: F401,F403
from .store_stand_in import stores_module

QUICK_TOPIC = True

ACME = "test_acme_k3f9"
MANA = ACME + ":mana"
saved = {MANA: {"tile_7": 5.0}}
game = SimpleNamespace(stores=stores_module([StoreSpec(MANA, ACME, "tile", 0.0, "mana")], saved).store_book())

# --- a read command shows the value its dotted state path reaches, the store's default where nothing is kept.
handler = mod_commands._reader(MANA, {"shows": [{"label": "Mana", "path": "stores.%s.tile_7" % MANA, "unit": "mana", "digits": 1},
                                               {"label": "Elsewhere", "path": "stores.%s.tile_9" % MANA, "unit": "mana"}]})
reply = handler(game, {}, {}, None)
check("a read command returns each row's stored value, and the default where the store holds none",
      reply["values"] == [{"label": "Mana", "value": 5.0, "unit": "mana"}, {"label": "Elsewhere", "value": 0.0, "unit": "mana"}], reply)

# --- the map shows a tile store as a layer on every row.
with mock.patch.object(screen_map, "map_report", side_effect=lambda sim, full=False: {"tiles": [{"tile": "tile_7"}, {"tile": "tile_9"}],
                                                                                    "next_door": [{"tile": "tile_8"}]}):
    shown = screen_map.map_screen(game, {"layer": MANA})
check("a layer puts the store's value on every tile row and every next-door row",
      [row["layer_value"] for row in shown["tiles"] + shown["next_door"]] == [5.0, 0.0, 0.0], shown)
check("a layer states the store, its unit, its default and the tiles that differ from the default",
      shown["layer"] == {"store": MANA, "unit": "mana", "default": 0.0, "tiles_off_default": {"tile_7": 5.0}}, shown["layer"])
check("a store that is not tile-keyed is not offered as a layer", game.stores.tile_layer("no_such_store") is None)

# --- tile control is the base game's control store (test_land_module reads it through the land module).
check("the base game declares control as a tile store with no owning mod", any(spec.name == "control" and spec.owner == "" and spec.keyed_by == "tile" for spec in content.base_store_declarations()))
