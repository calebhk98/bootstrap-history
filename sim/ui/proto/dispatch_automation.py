"""The automation command: what the automatic policies did, and why."""

from .command_registry import command
from sim.engine.ui_port import automation_audit


@command("automation", group="money", aliases=("audit", "autolog"),
         summary="what the automatic policies did lately, and why",
         usage=["automation", "automation <years>", "automation json"],
         options={"<years>": "how many years back (default: the year just played)", "json": "the raw reply"},
         description="One row per automatic action - hires, openings, reopenings, commissions, "
                     "mines, woodland - with the policy, the reason it fired and what it cost. "
                     "Reopening after a staffing closure is always on and is listed as such.")
def _cmd_automation(sim, nodes, cmd, ended):
    years = int(cmd.get("years") or 1)
    rows = automation_audit.rows(sim, years)
    return {"ok": True, "years": years, "rows": rows,
            "note": ("%d automatic action%s in the last %d year%s; 'policy' switches each one."
                     % (len(rows), "" if len(rows) == 1 else "s", years, "" if years == 1 else "s"))
            if rows else "no automatic action in that window ('policy' shows which are on)."}
