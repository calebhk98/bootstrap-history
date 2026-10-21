"""repeated_output through a game: the staffing paragraph of `why` is shown the first time and then a pointer, `full`
brings it back and the explained-once record survives a save and load; and the Options menu hands a line it did not
take back to the game prompt (Complaints/173, 157, 161). The rules are in test_repeated_output."""

from .harness import *  # noqa: F401,F403
from sim.tests import cli_in_process
from sim.ui import protocol as _protocol

_STAFF_PARAGRAPH = "not the crew that"


def _render(command_name, response):
    return _protocol.render_pretty(command_name, response)


def _dispatch(game, **command):
    return S._agent_dispatch(game, NODES, command)


game = sim(capital=1e6)
first_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom"))
second_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom"))
forced_why = _render("why", _dispatch(game, cmd="why", id="tex_horizontal_loom", full=True))
# presentation: the staffing paragraph and the pointer to `full`
check("`why` carries the staffing paragraph the first time, drops it for a pointer the second (ten lines shorter), and `full` restores it",
      _STAFF_PARAGRAPH in first_why and _STAFF_PARAGRAPH not in second_why and "why tex_horizontal_loom full" in second_why
      and len(first_why.splitlines()) - len(second_why.splitlines()) >= 10 and _STAFF_PARAGRAPH in forced_why,
      (first_why, second_why))

save_path = os.path.join(ROOT, "_repeated_output_tmp.json")
_protocol.save_state(game, save_path)
reloaded = sim(capital=1e6)
_protocol.load_state(reloaded, save_path)
os.remove(save_path)
after_reload = _render("why", _dispatch(reloaded, cmd="why", id="tex_horizontal_loom"))
check("the explained-once record survives save and load",
      _STAFF_PARAGRAPH not in after_reload, after_reload)

# --- 161: the Options menu hands a non-choice back to the game prompt.
completed = cli_in_process.run(
    ["play", "--kit", "rich_merchant", "--seed", "1", "--manual"],
    input_text="options\nstate\n", cwd=ROOT)
menu_output = completed.stdout
after_rejection = menu_output.split("not a choice")[-1]
# presentation: the menu echoes the line it did not take and shows once
check("the menu echoes the line it did not take",
      "not a choice" in menu_output and "state" in after_rejection.splitlines()[0],
      menu_output[-800:])
check("...shows the menu once, not again after the rejection",
      menu_output.count("OPTIONS") == 1, menu_output.count("OPTIONS"))
check("...and the rejected `state` then runs as a game command",
      "YEAR 100" in after_rejection, menu_output[-800:])
