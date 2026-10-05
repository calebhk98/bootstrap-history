"""`causes`: the cause rows behind wage, state notice and concern changes, from the cause book (Complaint 420)."""
from sim.engine.ui_port import cause_book
from .command_registry import command

KINDS = ("wage", "notice", "closure", "opening")


@command("causes", group="overview", aliases=("whyclosed",),
         summary="what moved wages, state notice and your concerns lately",
         usage=["causes", "causes <years>", "causes <kind>"],
         options={"<years>": "how many years back (default: the last two)",
                  "<kind>": "wage, notice, closure or opening"},
         description="One row per recorded cause: a wage change by what moved it, state notice by "
                     "the state, headcount, wealth or eminence, each concern that closed and why, "
                     "each opening or reopening with the revenue and upkeep it brought back.")
def _cmd_causes(sim, nodes, cmd, ended):
    argument = str(cmd.get("id") or cmd.get("years") or "").strip()
    kind = argument if argument in KINDS else None
    years = int(argument) if argument.isdigit() else 2
    rows = cause_book.rows(sim, kind, years)
    return {"ok": True, "years": years, "rows": rows,
            "note": ("%d cause row%s in the last %d year%s; 'figures wages' and 'figures state_notice' "
                     "add them up against the change." % (len(rows), "" if len(rows) == 1 else "s",
                                                          years, "" if years == 1 else "s"))
            if rows else "nothing recorded in that window."}
