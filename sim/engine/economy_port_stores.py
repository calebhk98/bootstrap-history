"""The opening stocks of durable stores of wealth, from what a civilisation's deposits yielded before the start.

Part of the port with economy_port_setup.py. Which good a resource yields is the catalogue's
`mine_demand_goods`; a resource that names several goods, or counts in a unit other than kilograms,
has no single good to hold and is reported as a gap rather than guessed.
"""
from sim.geography.api import mine_demand_goods, mined_before


def opening_store_values(world_map, tile_ids, start_year):
    """{good: {"workings": [[kg a year, years worked, years since the last output], ...], "gap": reason or ""}}
    for the good each mined resource yields."""
    stores = {}
    for resource_id, goods in sorted(mine_demand_goods(world_map).items()):
        if len(goods) != 1:
            for good in goods:
                stores[good] = {"workings": [], "gap": "%s yields several goods; none is chosen to hold its stock" % resource_id}
            continue
        mined = mined_before(tile_ids, resource_id, start_year, world_map)
        workings = [[each["output_per_year"], each["years_worked"], each["years_since_last_output"]] for each in mined["workings"]]
        if mined["unit"] != "kg":
            workings, gap = [], "%s is counted in %s, not kilograms" % (resource_id, mined["unit"])
        elif mined["deposits_in_tiles"] == 0:
            gap = "no known deposit of %s in the civilisation's tiles" % resource_id
        elif mined["unworked"]:
            gap = "not counted, no working date before the start or no known size: %s" % ", ".join(mined["unworked"])
        else:
            gap = ""
        stores[goods[0]] = {"workings": workings, "gap": gap}
    return stores
