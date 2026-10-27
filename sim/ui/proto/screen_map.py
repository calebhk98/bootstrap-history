"""The `map` screen: the tiles the nation holds and the ones beside them,
with names, terrain, people and the named deposits on each (Complaints/239).

Every figure is the engine's own: people per tile from settlement_tiles, the
town from home_town_population_estimate, the journey from relocation_quote,
deposits from sim.world.deposits.
"""
import functools

from sim.engine import ui_port

from sim.world import deposits as deposit_model
from sim.geography.api import regions_of_tiles, tile_names, tiles_held

mod_stores = ui_port.mod_stores

TILES_SHOWN_BY_DEFAULT = 12


@functools.lru_cache(maxsize=1)
def _deposits_by_tile():
    by_tile = {}
    for metal in deposit_model.METALS:
        for deposit in deposit_model.load_deposits(metal):
            by_tile.setdefault(deposit.tile, []).append({
                "name": deposit.name, "metal": metal,
                "depth": deposit.depth_class,
                "ore_grade_kg_per_tonne": deposit.ore_grade_kg_per_tonne})
    return by_tile


def tile_place(tile_id, world_map=None):
    """The readable fields every screen shows for one tile; `places` only when the map names some."""
    place = {"tile": tile_id, "name": tile_names.tile_name(tile_id),
             "region": tile_names.region_name(tile_id),
             "terrain": tile_names.terrain(tile_id)}
    named = tile_names.places_on(world_map, tile_id) if world_map is not None else []
    if named:
        place["places"] = named
    return place


def map_report(sim, full=False):
    held = sim.view("settlement_tiles")()
    base = sim.view("base_tile")()
    rows = []
    for tile_id in sorted(held, key=lambda name: (-held[name], name)):
        row = dict(tile_place(tile_id, sim.view("legacy_world_map")()), people=round(held[tile_id]),
                   deposits=_deposits_by_tile().get(tile_id, []))
        if tile_id == base:
            row["is_your_base"] = True
        else:
            quote = sim.view("relocation_quote")[tile_id]
            if quote is not None:
                row["days_from_your_base"] = round(quote[0])
        rows.append(row)
    next_door = {}
    for tile_id in held:
        for other in tile_names.neighbours(tile_id):
            if other not in held:
                next_door.setdefault(other, tile_names.tile_name(tile_id))
    door_rows = [dict(tile_place(tile_id, sim.view("legacy_world_map")()), beside=beside,
                      deposits=_deposits_by_tile().get(tile_id, []))
                 for tile_id, beside in sorted(next_door.items())]
    shown = rows if full else rows[:TILES_SHOWN_BY_DEFAULT]
    base_people = held.get(base, 0.0)
    return {
        "civilisation": sim.view("civilisation")().get("short_name", sim.view("civilisation")().get("name", "")),
        "population": round(sim.view("population")().total),
        "regions": [tile_names.region_names().get(region_id, region_id)
                    for region_id in regions_of_tiles(tiles_held(sim.view("civilisation")(), sim.view("legacy_world_map")()))],
        "you_are_based_at": dict(
            tile_place(base, sim.view("legacy_world_map")()), people=round(base_people),
            town_people=round(sim.view("home_town_population_estimate")())),
        "tiles": shown,
        "tiles_held": len(rows),
        "next_door": door_rows if full else door_rows[:TILES_SHOWN_BY_DEFAULT],
        "next_door_total": len(door_rows),
        "towns_note": ("the data names no towns: the one town you work in is "
                       "the figure above, an estimate, and a tile's name is "
                       "its country and number, not a historical place name"),
        "how": '{"cmd":"map","full":true} lists every tile; '
               '{"cmd":"move_base","to":"<tile>"} moves your base',
    }


def map_screen(sim, cmd):
    """The `map` reply; with `layer` naming a declared tile store, every tile row carries that store's value."""
    report = map_report(sim, full=bool(cmd.get("full")))
    layer = cmd.get("layer")
    if layer is None:
        return {"ok": True, **report}
    view = mod_stores.tile_layer(sim, str(layer))
    if view is None:
        tile_stores = sorted(name for name, spec in mod_stores.DECLARED.items() if spec.keyed_by == mod_stores.TILE)
        return {"ok": False, "cause": "unknown_layer", "error": "no tile store %r to show" % layer, "choices": tile_stores}
    for row in report["tiles"] + report["next_door"]:
        row["layer_value"] = view.get(row["tile"])
    report["layer"] = {"store": view.spec.name, "unit": view.spec.unit, "default": view.spec.default,
                       "tiles_off_default": dict(view.items())}
    return {"ok": True, **report}
