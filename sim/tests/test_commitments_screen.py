"""commitments_screen: the screen's figures are called on a stub game (the goal, literacy against its ceiling, the staff
reserve, the institutions open or closed); the rendering on a built reply. The game methods the screen calls are
checked to exist on `Sim`."""
QUICK_TOPIC = True

import types
from sim.tests import workforce_stand_in
from unittest import mock

from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry as _registry
from sim.ui.proto import screen_commitments
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.tests.ui_stand_in import Game

check("commitments is a registered command", _registry.resolve("commitments") is not None)

NODES_STUB = {"school": {"name": "School", "kind": "INSTITUTION"}, "mill": {"name": "Mill", "kind": "CONCERN"},
              "senate": {"name": "Senate", "kind": "INSTITUTION"}, "goal_node": {"name": "The Goal", "kind": "TECH"}}


def stub_game(**overrides):
    household = Game(reserve_craftsmen=3, reserve_scholars=1)
    game = Game(
        fog=False, goal="goal_node", goal_year=None, nodes=NODES_STUB, done={"school", "mill", "senate"}, policy={},
        workforce=household, staff={"reserve_craftsmen": 3, "reserve_scholars": 1}, state=Game(household=household), is_visible=lambda node_id: node_id != "senate",
        running=lambda node_id: node_id == "school", institution_units=lambda node_id: 2.0,
        literacy=lambda which: 0.1234567 if which == "literacy_general" else 0.05,
        literacy_ceiling_general=lambda: 0.4, literacy_ceiling_elite=lambda: 0.0)
    for name, value in overrides.items():
        setattr(game, name, value)
    return game


def report(game):
    with mock.patch.object(screen_commitments, "watched_rows", return_value=[]):
        return screen_commitments.commitments_report(game)


reply = report(stub_game())
check("the screen answers", reply.get("ok") is True, reply)
check("it names the goal and whether it is reached",
      reply["goal"] == {"id": "goal_node", "name": "The Goal", "reached": False, "year_reached": None}, reply["goal"])
check("it says when the goal was reached",
      report(stub_game(goal_year=130))["goal"]["reached"] is True and report(stub_game(goal_year=130))["goal"]["year_reached"] == 130, "not reached")
check("under fog the goal is withheld", report(stub_game(fog=True))["goal"]["id"] is None, report(stub_game(fog=True))["goal"])
check("it shows general literacy against its ceiling, as figures the education screen uses",
      reply["literacy"]["general"] == 0.1235 and reply["literacy"]["general_ceiling"] == 0.4
      and reply["literacy"]["share_of_ceiling_general"] == round(0.1234567 / 0.4, 4), reply["literacy"])
check("a literacy ceiling of nothing gives no share rather than dividing by it",
      reply["literacy"]["share_of_ceiling_elite"] is None, reply["literacy"])
check("it shows the reserve target and whether its policy is on",
      reply["reserve"] == {"craftsmen": 3, "scholars": 1, "policy_on": False}
      and report(stub_game(policy={"reserve_staff": True}))["reserve"]["policy_on"] is True, reply["reserve"])
check("it says the game has no secondary goals rather than inventing some",
      reply["secondary_goals"] == [] and "one goal" in reply["secondary_goals_note"], reply["secondary_goals_note"])  # presentation: the note's wording
rows = {row["id"]: row for row in reply["institutions"]}
check("a built institution is listed as open and a closed one as closed, and a concern is not an institution",
      set(rows) == {"school", "senate"} and rows["school"]["state"] == "open" and rows["senate"]["state"] == "closed", rows)
check("under fog an institution the player has not heard of is left out",
      {row["id"] for row in report(stub_game(fog=True))["institutions"]} == {"school"}, report(stub_game(fog=True))["institutions"])
check("the text screen has the sections",  # presentation: the screen's headings
      all(word in _render_pretty("commitments", reply) for word in ("GOAL", "RESERVE", "INSTITUTIONS")))

check("every game method the screen reads exists on Sim",
      all(callable(getattr(S.Sim, name, None)) for name in
          ("is_visible", "running", "institution_units", "literacy", "literacy_ceiling_general", "literacy_ceiling_elite")),
      [name for name in ("is_visible", "running", "institution_units", "literacy", "literacy_ceiling_general",
                         "literacy_ceiling_elite") if not callable(getattr(S.Sim, name, None))])
