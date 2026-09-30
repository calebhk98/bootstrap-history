"""repeated_output: Complaints/177 and 161 - long explanations shown once,
completions printed once, one household-wide staffing line, wrapped names,
and the Options menu handing unread lines back to the game prompt."""
import subprocess
import sys

from .harness import *  # noqa: F401,F403
from sim.engine import protocol as _protocol
from sim.engine.proto.render_screens_big import (
    _available_row, _state_completed_head_lines, _state_founder)

_STAFF_PARAGRAPH = "not the crew that"
_PRACTICE_PARAGRAPH = "rented room"


def _render(command_name, response):
    return _protocol.render_pretty(command_name, response)


def _dispatch(game, **command):
    return S._agent_dispatch(game, NODES, command)


# --- (a) the staffing paragraph is shown the first time, then a pointer.
game = sim(capital=1e6)
first_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom"))
second_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom"))
forced_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom", full=True))
check("first `why` carries the full staffing explanation",
      _STAFF_PARAGRAPH in first_why, first_why)
check("second `why` drops the paragraph and keeps a one-line pointer",
      _STAFF_PARAGRAPH not in second_why and "why tex_horizontal_loom full" in second_why,
      second_why)
check("...so the second screen is at least ten lines shorter",
      len(first_why.splitlines()) - len(second_why.splitlines()) >= 10,
      (len(first_why.splitlines()), len(second_why.splitlines())))
check("`why <id> full` brings the paragraph back",
      _STAFF_PARAGRAPH in forced_why, forced_why)
typed_command, _typed_error = _protocol.parse_typed("why tex_horizontal_loom full")
check("`why <id> full` parses to the id plus a full flag",
      typed_command == {"cmd": "why", "id": "tex_horizontal_loom", "full": True},
      typed_command)

save_path = os.path.join(ROOT, "_repeated_output_tmp.json")
_protocol.save_state(game, save_path)
reloaded = sim(capital=1e6)
_protocol.load_state(reloaded, save_path)
os.remove(save_path)
after_reload = _render("why", _dispatch(reloaded, cmd="why", id="tex_horizontal_loom"))
check("the explained-once record survives save and load",
      _STAFF_PARAGRAPH not in after_reload, after_reload)

# --- (b) the practice paragraph, shared between money and ventures.
game = sim(capital=1e6)
first_money = _render("money", _dispatch(game, cmd="money"))
second_money = _render("money", _dispatch(game, cmd="money"))
ventures_after = _render("ventures", _dispatch(game, cmd="ventures"))
forced_money = _render("money", _dispatch(game, cmd="money", full=True))
check("first `money` explains the practice",
      _PRACTICE_PARAGRAPH in first_money, first_money)
check("second `money` keeps the practice line but not the paragraph",
      _PRACTICE_PARAGRAPH not in second_money and "YOUR PRACTICE" in second_money,
      second_money)
check("`ventures` after `money` does not repeat it either",
      _PRACTICE_PARAGRAPH not in ventures_after and "YOUR PRACTICE" in ventures_after,
      ventures_after)
check("`money full` repeats it", _PRACTICE_PARAGRAPH in forced_money, forced_money)

# --- (c) a completion is printed once.
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

# --- (d) one household-wide staffing line.
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

# --- (e) long names wrap instead of being cut.
long_entry = {"id": "identity_cover", "name": "Establish a respectable identity",
              "cost": 10356, "founder_hours": 500}
row = _available_row(long_entry, 34, None)
check("a long name is wrapped onto further lines, none of it lost",
      all(word in row for word in ("Establish", "respectable", "identity")),
      row)
check("...and the first line still carries the id and the figures",
      row.splitlines()[0].startswith("identity_cover") and "10,356" in row.splitlines()[0],
      row)

# --- 161: the Options menu hands a non-choice back to the game prompt.
completed = subprocess.run(
    [sys.executable, os.path.join(HERE, "simulator.py"), "play", "--kit", "rich_merchant",
     "--seed", "1", "--manual"],
    input="options\nstate\n", capture_output=True, text=True, timeout=300, cwd=ROOT)
menu_output = completed.stdout
after_rejection = menu_output.split("not a choice")[-1]
check("the menu echoes the line it did not take",
      "not a choice" in menu_output and "state" in after_rejection.splitlines()[0],
      menu_output[-800:])
check("...shows the menu once, not again after the rejection",
      menu_output.count("OPTIONS") == 1, menu_output.count("OPTIONS"))
check("...and the rejected `state` then runs as a game command",
      "YEAR 100" in after_rejection, menu_output[-800:])
