"""Building roads and track between neighbouring tiles the nation holds."""

from .command_registry import command


@command("build_way", group="money",
         summary="build a road or railway between two neighbouring tiles",
         usage=["build_way road <tile> <tile>", "build_way road <tile> <tile> preview"],
         options={"<way>": "road or rail, whichever your people know how to build",
                  "<tile> <tile>": "two bordering tiles your nation holds",
                  "preview": "quote the labour, material and money without building"},
         description="Pays the labour and the stone (and iron, for rails) the terrain asks for, at "
                     "market prices. A built way is used by every journey and haul over that edge "
                     "that can use it; steeper ground costs more and the steepest cannot be built.")
def _cmd_build_way(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    way, tile_a, tile_b = str(cmd.get("way") or ""), str(cmd.get("from") or ""), str(cmd.get("to") or "")
    if not (way and tile_a and tile_b):
        return {"ok": False, "error": 'say what and between which tiles: {"cmd":"build_way","way":"road","from":"<tile>","to":"<tile>"}'}
    quote = sim.way_quote(tile_a, tile_b, way)
    if cmd.get("preview"):
        if quote is None:
            return {"ok": False, "error": "a %s cannot be built between %s and %s." % (way, tile_a, tile_b)}
        return {"ok": True, "preview": True, "way": way, "km": round(quote["km"], 1),
                "labour_hours": round(quote["labour_hours"]), "materials_tonnes": {
                    material: round(tonnes) for material, tonnes in quote["materials"].items()},
                "money": round(quote["money"])}
    built, message = sim.build_way(tile_a, tile_b, way)
    if not built:
        return {"ok": False, "error": message}
    return {"ok": True, "built": message, "capital": round(sim.capital, 1)}
