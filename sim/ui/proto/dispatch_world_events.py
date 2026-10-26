"""`world_events`: the dated world event log, the same for every seat (Complaint 493)."""
from .command_registry import command


@command("world_events", group="overview", aliases=("worldevents",),
         summary="what changed in the world lately: tile owners, floods, famines, with dates and causes",
         usage=["world_events", "world_events <years>", "world_events <kind>"],
         options={"<years>": "how many years back (default: the last ten)",
                  "<kind>": "tile_transfer, battle, flood, earthquake, bad_ruler or famine"},
         description="One row per record: its year, kind, the countries or seats involved, the tiles, the "
                     "cause and the figures. Every seat reads the same log.")
def _cmd_world_events(sim, nodes, cmd, ended):
    argument = str(cmd.get("id") or cmd.get("years") or "").strip()
    years = int(argument) if argument.isdigit() else 10
    kind = argument if argument and not argument.isdigit() else None
    rows = sim.view("world_events")(kind, sim.state.scenario.year - years)
    return {"ok": True, "years": years, "kind": kind, "events": rows,
            "note": "%d world event%s in the window." % (len(rows), "" if len(rows) == 1 else "s")}
