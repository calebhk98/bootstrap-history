"""commitments_screen: regression checks, run with `--only commitments_screen`."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry as _registry
from sim.ui.proto.render_typed import render_pretty as _render_pretty


def _ask(game):
    return S._agent_dispatch(game, NODES, {"cmd": "commitments"})


check("commitments is a registered command", _registry.resolve("commitments") is not None)
game = sim()
reply = _ask(game)
check("the screen answers", reply.get("ok") is True, reply)
check("it names the goal and whether it is reached",
      reply["goal"]["id"] == game.goal and reply["goal"]["reached"] is False, reply.get("goal"))
check("it shows general literacy against its ceiling, as figures the education screen uses",
      reply["literacy"]["general"] == round(float(game.civ["literacy_general"]), 4)
      and reply["literacy"]["general_ceiling"] == round(game.literacy_ceiling_general(), 4), reply.get("literacy"))
check("it shows the reserve target from the reserve command",
      reply["reserve"]["craftsmen"] == game.state.household.reserve_craftsmen
      and "policy_on" in reply["reserve"], reply.get("reserve"))
check("it says the game has no secondary goals rather than inventing some",
      reply["secondary_goals"] == [] and "one goal" in reply["secondary_goals_note"], reply.get("secondary_goals_note"))

institution = next(node_id for node_id, node in sorted(NODES.items()) if node.get("kind") == "INSTITUTION")
game.done.add(institution)
game.operating.add(institution)
game._done_changed()
rows = {row["id"]: row for row in _ask(game)["institutions"]}
check("a built institution is listed as open", rows.get(institution, {}).get("state") == "open", rows.get(institution))
game.operating.discard(institution)
game.mothballed.add(institution)
game._done_changed()
rows = {row["id"]: row for row in _ask(game)["institutions"]}
check("a closed institution is listed as closed", rows.get(institution, {}).get("state") == "closed", rows.get(institution))

fogged = sim()
fogged.fog = True
fogged.revealed = set()
fog_reply = _ask(fogged)
check("under fog the goal is withheld", fog_reply["goal"]["id"] is None, fog_reply["goal"])
check("the text screen has the sections",
      all(word in _render_pretty("commitments", reply) for word in ("GOAL", "RESERVE", "INSTITUTIONS")))
