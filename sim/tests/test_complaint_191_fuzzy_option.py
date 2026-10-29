"""Complaint 191: fuzzy estimates are a normal game option. The flag or menu choice beats the settings default, a fresh game takes the
default and a resumed one never does (`fuzzy_estimates_wanted`), the new-game menu's question defaults to the setting
(`_new_game_ask_fuzzy`), the options screen turns the option on one way (`turn_fuzzy_estimates_on`), and the setter draws the salt
once. The save keeping the option is test_fuzzy_estimates_saved_rule."""

QUICK_TOPIC = True

import contextlib
import io
import random
from types import SimpleNamespace

from .harness import check
from sim.tests import scenario_stand_in

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.ui import cli_interactive
from sim.ui.fuzzy_choice import fuzzy_estimates_wanted, turn_fuzzy_estimates_on

# ---- what a game starts with
check("the flag turns it on over a default of off", fuzzy_estimates_wanted(True, False, False) is True, None)
check("a flag that is off beats a default of on", fuzzy_estimates_wanted(False, False, True) is False, None)
check("a fresh game with no flag takes the settings default on", fuzzy_estimates_wanted(None, False, True) is True, None)
check("a fresh game with no flag and the default off starts with it off", fuzzy_estimates_wanted(None, False, False) is False, None)
check("a resumed game with no flag is not switched on from the default", fuzzy_estimates_wanted(None, True, True) is False, None)
check("the flag still applies when resuming", fuzzy_estimates_wanted(True, True, False) is True, None)

# ---- the new-game menu's question
def asked_with(config, answer):
    prompts = []

    def ask(prompt, options, default=None):
        prompts.append((prompt, options, default))
        return answer
    original = cli_interactive._ask
    cli_interactive._ask = ask
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            reply = cli_interactive._new_game_ask_fuzzy(config)
    finally:
        cli_interactive._ask = original
    return reply, prompts[0]


reply, (prompt, options, default) = asked_with({"default_fuzzy_estimates": True}, "y")
check("the menu's question defaults to y when the setting is on and answers what it is told", reply == "y" and default == "y" and options == ["y", "n"], default)
reply, (prompt, options, default) = asked_with({}, "n")
check("the menu's question defaults to n when no setting is held", reply == "n" and default == "n", default)
reply, _ = asked_with({}, None)
check("backing out of the menu's question answers None", reply is None, reply)

# ---- the options screen
def turn_on(answer):
    sim = scenario_stand_in.host()
    said = []
    turned = turn_fuzzy_estimates_on(sim, lambda prompt, options, default: answer, said.append, said.append)
    return sim, turned, said


sim, turned, said = turn_on("y")
check("answering y turns the option on", sim.view("legacy_fuzzy_estimates")() is True and turned is True, None)
for answer in ("n", None):
    sim, turned, said = turn_on(answer)
    check("an answer of %r leaves it off" % (answer,), sim.view("legacy_fuzzy_estimates")() is False and turned is False, None)

# ---- the setter
class Game(ForwardingPropertiesMixin):
    def __init__(self):
        stand_in = scenario_stand_in.host()
        self._scenario, self.rng, self.view, self.send = stand_in._scenario, stand_in.rng, stand_in.view, stand_in.send


game = Game()
game.fuzzy_estimates = True
salt = game.view("fuzzy_salt")()
check("turning it on stores it and draws a salt", game.fuzzy_estimates is True and salt > 0, salt)
game.fuzzy_estimates = True
check("turning it on again keeps the salt, so the figures drawn stay the same", game.view("fuzzy_salt")() == salt, None)
game = Game()
game.fuzzy_estimates = False
check("turning it off draws no salt", game.fuzzy_estimates is False and game.view("fuzzy_salt")() == 0, None)
