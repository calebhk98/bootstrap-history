"""Rules from the craftsmen wording scenario, each called on a stand-in: diffused printing makes the same schooling teach faster
where some school is open (`effective_schooling_flow`), and the specialist foreman a concern's row names is the foreman the
engine asks for (`specialist_foreman`)."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.diffusion.module import Diffusion
from sim.tests import module_harness
from sim.ui.proto.available_economics import specialist_foreman
from sim.tests.ui_stand_in import Game


def schooling(flow, printing):
    """The diffusion module whose schools give `flow` and over which printing has spread `printing`; and the fields asked."""
    asked = []

    class Schooled(Diffusion):
        def schooling_flow(self, field=None):
            asked.append(field)
            return flow

        def diffusion_index(self, kind):
            return printing
    return module_harness.build(Schooled), asked


game, asked = schooling(2.0, 0.0)
without = game.effective_schooling_flow()
game, asked = schooling(2.0, 1.0)
with_printing = game.effective_schooling_flow()
check("with no printing spread the schooling flow is what the schools give", without == 2.0, without)
check("diffused printing makes the same schools teach faster", with_printing > without, (without, with_printing))
game, asked = schooling(0.0, 1.0)
check("with no school open printing teaches nobody", game.effective_schooling_flow() == 0.0, None)
game, asked = schooling(2.0, 0.5)
game.effective_schooling_flow("literacy_general")
check("the figure asked about is passed to the schools that teach it", asked == ["literacy_general"], asked)

check("a concern's row names the foreman trade and his share of the year, rounded",
      specialist_foreman(Game(venture_foreman=lambda node_id: ("glassblower", 0.254)), "mirror") == {"trade": "glassblower", "fte": 0.25}, None)
check("a concern that needs no specialist names none", specialist_foreman(Game(venture_foreman=lambda node_id: (None, 0.0)), "plain") is None, None)
