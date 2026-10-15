"""Metals a civilisation needs but has no deposit of within reach (Complaint 516).

Pure data check, no civilisation or ore ids. For each resource the map's catalogue gives ore goods for, a
civilisation demands it when its coin is that metal, a household need names a good the resource yields, or a
technique it can run (ungated, or gated on a node it holds) consumes one. The demand goods of a resource are
its ore goods, the goods its smelting recipes make and the goods its catalogue row names as mine demand.
A civilisation is supplied when a deposit of the resource, already worked at its start year, stands on a
tile within `ore_supply_reach_level` of the tiles it holds. A civilisation lists the metals it imported
instead in `imported_ores` ({resource: reason}); an unlisted shortfall, and a listed metal that is in fact
supplied, are reported as warnings.

Used by `simulator.py validate`, and importable for tests.
"""
import sim.geography.api as geography

MINIMUM_REASON_LENGTH = 30


def demand_goods(ore_goods, mine_demand_goods, production):
    """{resource id: set of goods whose use is a demand for that resource}."""
    goods = {}
    for resource_id, by_ore in ore_goods.items():
        wanted = set(by_ore) | set(mine_demand_goods.get(resource_id, ()))
        for recipe_ids in by_ore.values():
            for recipe_id in recipe_ids:
                wanted.update(((production.get(recipe_id) or {}).get("outputs") or {}))
                wanted.add(recipe_id)
        goods[resource_id] = wanted
    return goods


def demanded_resources(civilisation, goods_by_resource, production, need_goods):
    """The resources whose goods the civilisation's coin, households or runnable techniques consume."""
    held = set(civilisation.get("starting_techs") or ())
    coin = (civilisation.get("coin_standard") or {}).get("material")
    consumed = set(need_goods)
    if coin:
        consumed.add(coin)
    for entry in production.values():
        gate = entry.get("requires_node")
        if gate is None or gate in held:
            consumed.update(entry.get("inputs") or ())
    return {resource_id for resource_id, goods in goods_by_resource.items() if goods & consumed}


def resources_in_reach(deposits_by_resource, levels, year, limit):
    """The resources with a deposit, worked by `year`, on a tile at most `limit` levels away.
    `deposits_by_resource` is {resource id: [(tile id, first_worked or None)]}; `levels` {tile id: level}."""
    return {resource_id for resource_id, deposits in deposits_by_resource.items()
            if any((first is None or first <= year) and levels.get(tile_id, limit + 1) <= limit
                   for tile_id, first in deposits)}


def deposits_by_resource(resource_ids, world_map=None):
    """{resource id: [(tile id, first_worked or None)]} from the map's catalogue."""
    rows = geography.open_map().catalogue("deposits") if world_map is None else world_map.catalogue("deposits")
    return {resource_id: [(deposit["tile_id"], rows[deposit["id"]].get("first_worked"))
                          for deposit in geography.known_deposits(resource_id, world_map)]
            for resource_id in resource_ids}


def supplied_resources(civilisation, resource_ids, world_map=None):
    """The resources among `resource_ids` with a worked deposit within reach of the civilisation's tiles."""
    held_tiles = geography.tiles_held(civilisation, world_map)
    limit = int(geography.parameter_value("ore_supply_reach_level", world_map))
    levels = geography.tile_reach_levels(held_tiles, civilisation.get("starting_techs") or (), world_map)
    return resources_in_reach(deposits_by_resource(resource_ids, world_map), levels, int(civilisation["year"]), limit)


def ore_reach_findings(civilisations, production, need_goods, world_map=None):
    """(errors, warnings) per civilisation: a demanded metal with no deposit in reach needs a reason under
    `imported_ores`; a reason for a metal that is supplied, or not demanded, is stale. Short reasons are errors."""
    ore_goods = geography.ore_goods(world_map)
    goods_by_resource = demand_goods(ore_goods, geography.mine_demand_goods(world_map), production)
    errors, warnings = [], []
    for name, civilisation in sorted(civilisations.items()):
        declared = civilisation.get("imported_ores") or {}
        demanded = demanded_resources(civilisation, goods_by_resource, production, need_goods)
        missing = demanded - supplied_resources(civilisation, sorted(demanded), world_map)
        for resource_id in sorted(missing):
            reason = declared.get(resource_id)
            text = "%s: demands %s but no deposit of it lies within reach" % (name, resource_id)
            if reason is None:
                warnings.append(text + "; add a deposit to data/world/geography/deposits/, or declare it in "
                                "imported_ores with a reason")
            elif len(reason) < MINIMUM_REASON_LENGTH:
                errors.append(text + "; its imported_ores reason is too short to be a reason")
        for resource_id in sorted(set(declared) - missing):
            warnings.append("%s: imported_ores lists %s, which it has a deposit of in reach or does not demand; "
                            "remove the entry" % (name, resource_id))
    return errors, warnings
