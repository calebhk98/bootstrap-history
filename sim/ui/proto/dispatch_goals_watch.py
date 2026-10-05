"""The in-game goals command: progress toward the formal goal and the goals you watch (Complaint 268)."""
from .command_registry import command
from .goals_watch import goals_report, promote, unwatch, watch


@command("goals", group="society",
         summary="progress toward the formal goal and any goals you watch",
         usage=["goals", "goals watch <goal id or name>", "goals unwatch <goal id or name>", "goals promote [<goal id or name>]",
                '{"cmd":"goals","action":"watch","goal":"<id>"}'],
         options={"watch <goal>": "also track a goal from the list, by id or name",
                  "unwatch <goal>": "stop tracking it",
                  "promote [<goal>]": "once the formal goal is reached, make a watched goal the formal one"},
         description="Done over needed for each goal, counting what its prerequisites require. "
                     "Under fog a goal you have not heard of shows as a count only. A watched goal "
                     "is tracked here; the formal goal stays the one the score uses.")
def _cmd_goals(sim, nodes, cmd, ended):
    action = str(cmd.get("action") or "").strip().lower()
    if not action:
        return goals_report(sim)
    goal = str(cmd.get("goal") or "").strip()
    if action == "promote":
        return promote(sim, goal)
    if action not in ("watch", "unwatch") or not goal:
        return {"ok": False, "error": "say 'goals watch <goal>', 'goals unwatch <goal>' or 'goals promote'; bare 'goals' lists them"}
    return (watch if action == "watch" else unwatch)(sim, goal)
