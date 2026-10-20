"""A setup rebuilt from the saved opening scales the needs by the opening's literacy, not the literacy the
society has reached since: a resumed game then plays the same year the unbroken one does."""
from .harness import *  # noqa: F401,F403
from sim.engine import economy_port_setup

game = sim(civ="norse_900ad", events=False)
opening = economy_port_setup.opening_values(game)
first = economy_port_setup.build_setup(game, opening)
original_literacy = game.literacy
game.literacy = lambda field, *args, **kwargs: original_literacy(field, *args, **kwargs) * 0.5 + 0.01
rebuilt = economy_port_setup.build_setup(game, opening)


def weights(setup):
    return [need.budget_weight for need in setup.basket.needs]


check("the opening saves the literacy the needs were scaled by",
      set(opening["literacy"]) == {"literacy_general", "literacy_elite"})
check("a setup rebuilt after literacy moved has the first setup's need weights", weights(rebuilt) == weights(first))
