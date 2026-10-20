"""Scenario for the `commitments` screen in a whole game: the command answers from a running game and reads the
literacy, reserve and institution figures other screens use. The figures themselves are in test_commitments_screen."""
from .harness import *  # noqa: F401,F403

game = sim()
institution = next(node_id for node_id, node in sorted(NODES.items()) if node.get("kind") == "INSTITUTION")
game.done.add(institution)
game.operating.add(institution)
game._done_changed()
reply = S._agent_dispatch(game, NODES, {"cmd": "commitments"})
rows = {row["id"]: row for row in reply.get("institutions", [])}
check("scenario: the commitments command answers from a game with its goal, the education screen's literacy, the reserve and an open institution",
      reply.get("ok") is True and reply["goal"]["id"] == game.goal
      and reply["literacy"]["general"] == round(float(game.literacy("literacy_general")), 4)
      and reply["reserve"]["craftsmen"] == game.state.household.reserve_craftsmen
      and rows.get(institution, {}).get("state") == "open", reply)
