"""Prospecting a held tile for a material's hidden deposits."""

from .command_registry import command


@command("prospect", group="money",
         summary="prospect a tile you hold for deposits of a material",
         usage=["prospect <tile> <material> <person_days>"],
         options={"<tile>": "a tile your nation holds",
                  "<material>": "a mined material, such as coal or iron",
                  "<person_days>": "the effort to spend; more effort finds more of what is there"},
         description="Pays prospectors at the mining wage and keeps the deposits found. A mine names a "
                     "deposit you have found, and what it can raise a year is bounded by that deposit's "
                     "size; the known mines of the tiles you hold are already found. More effort on the same "
                     "tile finds a superset of what less effort found.")
def _cmd_prospect(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    tile, material = str(cmd.get("tile") or ""), str(cmd.get("material") or "")
    try:
        person_days = float(cmd.get("person_days") or 0.0)
    except (TypeError, ValueError):
        person_days = 0.0
    if not (tile and material):
        return {"ok": False, "error": 'say where and for what: {"cmd":"prospect","tile":"<tile>","material":"coal","person_days":2000}'}
    ok, message = sim.prospect_deposits(tile, sim._normalize_material_name(material), person_days)
    if not ok:
        return {"ok": False, "error": message}
    return {"ok": True, "prospected": message, "capital": round(sim.capital, 1)}
