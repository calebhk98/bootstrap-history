"""The saving command: a planned project and the cash target an actor is putting money by for."""

from .command_registry import command
from .saving_plan import saving_plan


@command("saving", group="money", aliases=("save_for", "savings"),
         summary="put money by for a planned project",
         usage=["saving", "saving <id>", "saving <id> <amount>", "saving off"],
         options={"<id>": "the project you mean to start", "<amount>": "cash to reach (default: its cost)",
                  "off": "stop saving"},
         description="Marks a planned project and a savings target. 'stuck' then stops advising "
                     "you to start the cheapest thing, and shows the year the target is reached "
                     "at your current net income. Bare saving shows the plan.")
def _cmd_saving(sim, nodes, cmd, ended):
    household = sim.state.household
    if cmd.get("off"):
        household.saving_for = None
        household.saving_target = 0.0
    elif cmd.get("id") is not None:
        node_id = cmd["id"]
        if node_id not in nodes:
            return {"ok": False, "error": "unknown node id %r. 'available' lists what you could begin" % node_id}
        target = cmd.get("target")
        if target is None:
            target = sim.project_cost(node_id)
        elif isinstance(target, bool) or not isinstance(target, (int, float)) or target < 0:
            return {"ok": False, "error": "the target is an amount of money, zero or more"}
        household.saving_for = node_id
        household.saving_target = float(target)
    return {"ok": True, "saving": saving_plan(sim),
            "note": "'stuck' shows the year the target is reached; 'saving off' stops."}
