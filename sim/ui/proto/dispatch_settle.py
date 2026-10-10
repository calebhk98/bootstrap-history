"""The settle and colonies commands: found a colony on a tile beyond the country's own, and list those held."""

from .command_registry import command

CANDIDATES_SHOWN = 15


@command("settle", group="projects",
         summary="found a colony on a tile beyond your country's",
         usage=["settle", "settle <tile>"],
         options={"<tile>": "a tile id from the listing"},
         description="With no tile, lists the tiles settlers could reach (bordering what you hold, or by sea on "
                     "a coast), best land first, and what sending settlers costs. With a tile, sends settlers "
                     "from the country's working-age people, outfitted at your cost; they and their children "
                     "are a people of their own, fed by that tile's land as far as their own hands work it. "
                     "Needs a technology that provides for settlement.")
def _cmd_settle(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be founded" % ended}
    tile = cmd.get("tile")
    if tile:
        ok, text = sim.found_colony(str(tile))
        return {"ok": True, "message": text, "colonies": sim.colony_rows()} if ok else {"ok": False, "error": text}
    chosen = sim.settlement_spec(by_sea=False) or sim.settlement_spec(by_sea=True)
    if chosen is None:
        return {"ok": False, "error": "you know no way to send settlers yet"}
    spec = chosen[1]
    by_sea = bool(sim.settlement_spec(by_sea=True))
    return {"ok": True, "settlers": spec["settlers"],
            "outfit_cost": round(sim.settlement_outfit_cost(spec), 1),
            "tiles": sim.settlement_candidates(by_sea)[:CANDIDATES_SHOWN],
            "colonies": sim.colony_rows()}


@command("colonies", group="projects",
         summary="the colonies you hold",
         usage=["colonies"], options={},
         description="Each colony's tile, the year it was founded, its people and the most its land could feed.")
def _cmd_colonies(sim, nodes, cmd, ended):
    return {"ok": True, "colonies": sim.colony_rows()}
