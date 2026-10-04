"""The pursue command: begin what is startable on a goal's route, within the caps given."""

from .command_registry import command
from .dispatch_ventures import _cmd_rush
from .pursue import CAP_KEYS, FOG_REFUSAL, ORDER_TEXT, resolve_goal, route_order, rush_command


@command("pursue", group="projects", fog_hidden=True,
         summary="start what is startable on the way to a goal",
         usage=["pursue", "pursue <goal> max_total_cost:<n> max_annual_draw:<n> reserve_cash:<n> limit:<n>",
                "pursue preview"],
         options={"<goal>": "the goal or any target (default: the current goal)",
                  "max_total_cost": "cap total money", "max_annual_draw": "cap yearly draw",
                  "reserve_cash": "keep this much back", "limit": "cap the count",
                  "preview": "show what it would start, starting nothing"},
         description="A rush limited to the goal's route, longest remaining chain first. Every refusal, "
                     "exclusion and cap of 'rush' applies. Not available under fog of war.")
def _cmd_pursue(sim, nodes, cmd, ended):
    if sim.fog:
        return {"ok": False, "error": FOG_REFUSAL}
    goal, error = resolve_goal(sim, cmd.get("goal", cmd.get("id")))
    if error:
        return {"ok": False, "error": error}
    if goal in sim.done:
        return {"ok": False, "error": "%s is already done" % nodes[goal]["name"]}
    candidates = route_order(sim, goal)
    pursuit = {"goal": goal, "name": nodes[goal]["name"], "order": ORDER_TEXT,
               "startable_on_route": len(candidates)}
    if not candidates:
        return {"ok": True, "started": [], "count_started": 0, "pursue": pursuit,
                "note": "nothing on the route to %s is startable today; 'path %s' shows what blocks it"
                        % (nodes[goal]["name"], goal)}
    rush_cmd = rush_command(candidates, caps={key: cmd.get(key) for key in CAP_KEYS},
                            limit=cmd.get("limit"), preview=cmd.get("preview"))
    result = _cmd_rush(sim, nodes, rush_cmd, ended)
    if result.get("ok"):
        result["pursue"] = pursuit
    return result
