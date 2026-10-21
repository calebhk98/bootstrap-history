"""repeated_output: Complaints/173 and 157 - long explanations shown once, completions printed once, one household-wide
staffing line and wrapped names, each on a built reply or a stand-in game (no game). Through a game: the `why`
paragraph and the Options menu are test_repeated_output_scenario."""
from types import SimpleNamespace

from .harness import check, NODES

from sim.ui import protocol as _protocol
from sim.ui.proto.explain_once import already_explained
from sim.ui.proto.render_screen_available import _available_row
from sim.ui.proto.render_screen_state import _state_completed_head_lines
from sim.ui.proto.render_screen_state_blocks import _state_founder

QUICK_TOPIC = True


def _game(year=100):
    return SimpleNamespace(year=year, state=SimpleNamespace(seat_progress=SimpleNamespace(_said_explanations=None)))


# --- (a) a long explanation is shown the first time, then a pointer
game = _game()
check("the first time a topic is asked for it is not yet explained", already_explained(game, "staffing_share", {}) is False)
check("the second time it is, and the topic is remembered with the year it was first shown",
      already_explained(game, "staffing_share", {}) is True and game.state.seat_progress._said_explanations == {"staffing_share": 100})
check("asking for `full` shows it again", already_explained(game, "staffing_share", {"full": True}) is False)
check("a different topic is independent", already_explained(game, "staffing_means", {}) is False)
game.year = 105
already_explained(game, "staffing_share", {})
check("the year of first showing is not overwritten later", game.state.seat_progress._said_explanations["staffing_share"] == 100)
check("the first time with `full` still marks it shown",
      already_explained(_game(), "x", {"full": True}) is False)
fresh = _game()
already_explained(fresh, "x", {"full": True})
check("...so a plain ask afterwards is a repeat", already_explained(fresh, "x", {}) is True)

typed_command, _typed_error = _protocol.parse_typed("why tex_horizontal_loom full")
check("`why <id> full` parses to the id plus a full flag",
      typed_command == {"cmd": "why", "id": "tex_horizontal_loom", "full": True}, typed_command)

# --- (c) a completion is printed once
shed_name = NODES["tx2_shed"]["name"]
step_reply = {"completed": [{"year": 100, "name": shed_name}],
              "events": [{"year": 100, "message": "completed: " + shed_name}]}
step_lines = _state_completed_head_lines(step_reply)
check("a plain completion prints once, not as COMPLETED plus DURING",
      sum(shed_name in line for line in step_lines) == 1, step_lines)
closed_reply = {"completed": [{"year": 100, "name": "Loom"}],
                "events": [{"year": 100, "message":
                            "completed: Loom. STATUS: CLOSED / NOT OPERATING. "
                            "Nothing is earning yet. Open it ('open x') to begin."},
                           {"year": 100, "message": "something else happened"}]}
closed_lines = _state_completed_head_lines(closed_reply)
check("a concern's completion prints once and keeps the open hint",
      sum("Loom" in line for line in closed_lines) == 1
      and any("open x" in line and "COMPLETED" in line for line in closed_lines),
      closed_lines)
check("...and other events are untouched",
      any("something else happened" in line for line in closed_lines), closed_lines)

# --- (d) one household-wide staffing line
warnings = [{"name": name, "within": 1.3, "of": "craftsmen", "one_loss_closes_it": False,
             "headline": "%s has 1.3 spare craftsmen before it closes" % name}
            for name in ("Mill", "Loom", "Forge")]
warning_text = "\n".join(_state_founder({"supervision_close_to_the_edge": warnings}))
check("equal spare-craftsmen warnings become one line naming every concern",
      warning_text.count("1.3") == 1
      and all(name in warning_text for name in ("Mill", "Loom", "Forge")),
      warning_text)
mixed = warnings[:1] + [{"name": "Kiln", "within": 0.5, "of": "craftsmen",
                         "one_loss_closes_it": True,
                         "headline": "Kiln has no spare craftsmen: losing one more closes it"}]
mixed_text = "\n".join(_state_founder({"supervision_close_to_the_edge": mixed}))
check("a different warning keeps its own line",
      "Kiln has no spare craftsmen" in mixed_text and "Mill has 1.3" in mixed_text,
      mixed_text)

# --- (e) long names wrap instead of being cut
long_entry = {"id": "identity_cover", "name": "Establish a respectable identity",
              "cost": 10356, "founder_hours": 500}
row = _available_row(long_entry, 34, None)
check("a long name is wrapped onto further lines, none of it lost",
      all(word in row for word in ("Establish", "respectable", "identity")),
      row)
check("...and the first line still carries the id and the figures",
      row.splitlines()[0].startswith("identity_cover") and "10,356" in row.splitlines()[0],
      row)
