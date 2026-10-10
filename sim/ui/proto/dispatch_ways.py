"""Building roads, track, canals and bridges between neighbouring tiles the nation holds, and ports on a tile."""

from .command_registry import command


@command("build_way", group="money",
         summary="build a road, railway, canal, bridge or port",
         usage=["build_way road <tile> <tile>", "build_way road <tile> <tile> preview", "build_way port <tile>"],
         options={"<way>": "road, rail, canal, bridge (over a river between two tiles on it) or port (on a "
                           "coast tile without a natural harbour), whichever your people know how to build",
                  "<tile> <tile>": "two bordering tiles your nation holds (a port: one tile)",
                  "preview": "quote the labour, material, money and years without building"},
         description="Pays the labour and the stone, timber and iron the terrain asks for, at market "
                     "prices, and takes a crew from the labour market for the years it needs. A built way "
                     "is used by every journey and haul over that edge that can use it; steeper ground "
                     "costs more, ground beyond the natural limit is cut and banked (engineered) at a "
                     "higher cost, and the steepest cannot be built. A railway needs a bridge where it "
                     "crosses a river; a port joins a coast tile to the sea.")
def _cmd_build_way(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    way, tile_a, tile_b = str(cmd.get("way") or ""), str(cmd.get("from") or ""), str(cmd.get("to") or "")
    tile_b = tile_b or tile_a
    if not (way and tile_a):
        return {"ok": False, "error": 'say what and between which tiles: {"cmd":"build_way","way":"road","from":"<tile>","to":"<tile>"}'}
    quote = sim.way_quote(tile_a, tile_b, way)
    if cmd.get("preview"):
        if quote is None:
            return {"ok": False, "error": "a %s cannot be built between %s and %s." % (way, tile_a, tile_b)}
        return {"ok": True, "preview": True, "way": way, "km": round(quote["km"], 1),
                "labour_hours": round(quote["labour_hours"]), "materials_tonnes": {
                    material: round(tonnes) for material, tonnes in quote["materials"].items()},
                "money": round(quote["money"]), "years": round(quote["years"], 1),
                "engineered": quote["engineered"]}
    built, message = sim.build_way(tile_a, tile_b, way)
    if not built:
        return {"ok": False, "error": message}
    return {"ok": True, "built": message, "capital": round(sim.capital, 1)}
