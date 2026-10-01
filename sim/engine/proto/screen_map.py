"""The `map` screen: the tiles the nation holds and the ones beside them,
with names, terrain, people and the named deposits on each (Complaints/243).

Every figure is the engine's own: people per tile from settlement_tiles, the
town from home_town_population_estimate, the journey from relocation_quote,
deposits from sim.world.deposits.
"""
import functools

from sim.world import deposits as deposit_model
from sim.world import tile_names

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


def tile_place(tile_id):
    """The readable fields every screen shows for one tile."""
    return {"tile": tile_id, "name": tile_names.tile_name(tile_id),
            "region": tile_names.region_name(tile_id),
            "terrain": tile_names.terrain(tile_id)}


def map_report(sim, full=False):
    held = sim.settlement_tiles()
    base = sim.base_tile()
    rows = []
    for tile_id in sorted(held, key=lambda name: (-held[name], name)):
        row = dict(tile_place(tile_id), people=round(held[tile_id]),
                   deposits=_deposits_by_tile().get(tile_id, []))
        if tile_id == base:
            row["is_your_base"] = True
        else:
            days, _hours, _money = sim.relocation_quote(tile_id)
            row["days_from_your_base"] = round(days)
        rows.append(row)
    next_door = {}
    for tile_id in held:
        for other in tile_names.neighbours(tile_id):
            if other not in held:
                next_door.setdefault(other, tile_names.tile_name(tile_id))
    door_rows = [dict(tile_place(tile_id), beside=beside,
                      deposits=_deposits_by_tile().get(tile_id, []))
                 for tile_id, beside in sorted(next_door.items())]
    shown = rows if full else rows[:TILES_SHOWN_BY_DEFAULT]
    base_people = held.get(base, 0.0)
    return {
        "civilisation": sim.civ.get("short_name", sim.civ.get("name", "")),
        "population": round(sim.population.total),
        "regions": [tile_names._region_names().get(region_id, region_id)
                    for region_id in sim.civ.get("home_regions") or []],
        "you_are_based_at": dict(
            tile_place(base), people=round(base_people),
            town_people=round(sim.home_town_population_estimate())),
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
