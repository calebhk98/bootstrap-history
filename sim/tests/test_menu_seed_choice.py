"""The new-game menu's seed question (blank draws a random seed, a number is used, a word is kept, settings may hold a
default). Complaint 640: the question and the resolver are called directly, no game; the CLI run is
test_menu_seed_choice_scenario."""
import builtins
import os

from .harness import check

from sim.ui import cli_interactive

QUICK_TOPIC = True


def _ask_seed(answers, config=None):
    """What the seed question returns for these typed answers, with settings `config`."""
    remaining = list(answers)
    real_input = builtins.input
    builtins.input = lambda prompt="": remaining.pop(0)
    try:
        return cli_interactive._new_game_ask_seed(config or {})
    finally:
        builtins.input = real_input


# ---- the seed rules
blank_answer = _ask_seed([""])
check("menu: a blank seed asks for a random one", blank_answer is None, blank_answer)
saved_default = os.environ.pop(cli_interactive.DEFAULT_SEED_ENV, None)
try:
    drawn = {cli_interactive.resolve_seed(None) for _ in range(3)}
finally:
    if saved_default is not None:
        os.environ[cli_interactive.DEFAULT_SEED_ENV] = saved_default
check("menu: no seed given draws a fresh random one each time", len(drawn) > 1, drawn)
word_answer = _ask_seed(["Rome42"])
check("menu: a word seed is accepted and kept as typed, in lower case", word_answer == "rome42", word_answer)
retyped = _ask_seed(["two words", "77"])
check("menu: a seed with a space is asked again", retyped == 77, retyped)
configured_answer = _ask_seed([""], {"default_seed": 9001})
check("menu: a blank answer takes the seed set in settings", configured_answer == 9001, configured_answer)
quit_answer = _ask_seed(["q"])
check("menu: a quit answer backs out", quit_answer is False, quit_answer)

