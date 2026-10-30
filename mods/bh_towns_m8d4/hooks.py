"""Town table commands: list towns, and move the base to a town by name.

The towns are a catalogue of this mod's map overlay (data/world/geography/towns/), read through the game's merged map.
Nothing here writes engine state: `go` resolves a name to a tile and runs the ordinary `move_base` command, so its
cost, refusals and effects are the shipped ones.
"""
from sim.mod_api import MoveBase


# Heuristic (retire: later dated snapshots added to `sizes`, or a growth model): a figure older than this many
# years is flagged `stale` rather than hidden, so it is visibly dated.
STALE_AFTER_YEARS = 300


def _snapshot(town, year):
    """The town's latest size record dated at or before `year`; None before its earliest record."""
    earlier = [record for record in town["sizes"] if record["year"] <= year]
    return max(earlier, key=lambda record: record["year"]) if earlier else None


def _names(town):
    return [town["name"]] + list(town.get("also_called", ()))


def _matches(town, words):
    needle = words.strip().lower()
    return needle == town["tile"] or any(needle in name.lower() for name in _names(town))


def _present(towns, year):
    """[(town, snapshot)] for the towns that exist in `year`."""
    return [(town, record) for town in towns for record in [_snapshot(town, year)] if record is not None]


def _row(access, town, record, held):
    row = {"town": record.get("name", town["name"]), "tile": town["tile"], "people": record["people"],
           "people_low": record["low"], "people_high": record["high"],
           "size_year": record["year"], "years_old": access.view("year")() - record["year"],
           "confidence": record["conf"], "source": record["source"], "held": town["tile"] in held}
    if row["years_old"] > STALE_AFTER_YEARS:
        row["stale"] = True
    names = [name for name in _names(town) if name != row["town"]]
    if names:
        row["also_called"] = names
    if town.get("note"):
        row["note"] = town["note"]
    if town["tile"] == access.view("base_tile")():
        row["is_your_base_tile"] = True
    elif row["held"]:
        quote = access.view("relocation_quote")[town["tile"]]
        if quote is not None:
            row["days_from_your_base"] = round(quote[0])
    return row


def _towns(access):
    return list(access.view("map_catalogue")("towns").values())


def register(api):
    api.reads("year", "base_tile", "relocation_quote", "settlement_tiles", "map_catalogue", "acting_balance")
    api.sends(MoveBase)

    @api.command("towns", group="labour", shape="text",
                 summary="list the named towns on your tiles, or find one by name or tile",
                 usage=["towns", "towns <name or tile>"],
                 options={"<name or tile>": "part of a town's name, or a tile id; also finds towns outside your nation"},
                 description="Lists towns from the mod's town table with their size at the nearest dated "
                             "figure, its range, source and confidence, and the days from your base. "
                             "A tile holds several towns at once; the sizes are cited start-date figures, "
                             "not the simulation's own town estimate.")
    def towns(access, nodes, cmd, ended):
        held = access.view("settlement_tiles")()
        words = str(cmd.get("text") or "").strip()
        found = [(town, record) for town, record in _present(_towns(access), access.view("year")())
                 if (_matches(town, words) if words else town["tile"] in held)]
        rows = sorted((_row(access, town, record, held) for town, record in found),
                      key=lambda row: (-row["people"], row["town"]))
        if not rows:
            return {"ok": True, "towns": [], "note": "no town in the table matches" if words
                    else "the table names no town on your tiles"}
        return {"ok": True, "towns": rows,
                "how": '{"cmd":"bh_towns_m8d4:go","text":"<town>"} moves your base to the town\'s tile'}

    @api.command("go", group="labour", shape="text",
                 summary="move your base to a town by name",
                 usage=["go <town>"], options={"<town>": "a town from `towns`"},
                 description="Finds the town in the town table and runs the ordinary move to its tile, "
                             "with the same costs and refusals.")
    def go(access, nodes, cmd, ended):
        if ended:
            return {"ok": False, "error": "the run has ended (%s)" % ended}
        words = str(cmd.get("text") or "").strip()
        if not words:
            return {"ok": False, "error": "name a town; `towns` lists them"}
        found = [town for town, _record in _present(_towns(access), access.view("year")()) if _matches(town, words)]
        exact = [town for town in found if words.lower() in (name.lower() for name in _names(town))]
        found = exact or found
        if not found:
            return {"ok": False, "error": "no town called %r in the table; `towns` lists them" % words}
        if len({town["tile"] for town in found}) > 1:
            return {"ok": False, "error": "%r matches several towns on different tiles: %s" %
                    (words, ", ".join("%s (%s)" % (town["name"], town["tile"]) for town in found))}
        town = found[0]
        moved, message = access.send(MoveBase(town["tile"]))
        if not moved:
            return {"ok": False, "error": message}
        return {"ok": True, "moved": message, "based_at": access.view("base_tile")(),
                "capital": round(access.view("acting_balance")(), 1), "town": town["name"],
                "note": "the tile holds more than one town; your base is the tile"}
