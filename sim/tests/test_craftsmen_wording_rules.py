"""Rules from the craftsmen wording scenario, each called on a stand-in: diffused printing makes the same schooling teach faster
where some school is open (`effective_schooling_flow`), and the specialist foreman a concern's row names is the foreman the
engine asks for (`specialist_foreman`)."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.society_adoption import AdoptionMixin
from sim.ui.proto.available_economics import specialist_foreman


def schooling(flow, printing):
    asked = []
    game = SimpleNamespace(PRINTING_DIFFUSION_SCHOOLING_BOOST=AdoptionMixin.PRINTING_DIFFUSION_SCHOOLING_BOOST,
                           _schooling_flow=lambda field=None: asked.append(field) or flow, information_diffusion_index=lambda: printing)
    return game, asked


game, asked = schooling(2.0, 0.0)
without = AdoptionMixin.effective_schooling_flow(game)
game, asked = schooling(2.0, 1.0)
with_printing = AdoptionMixin.effective_schooling_flow(game)
check("with no printing spread the schooling flow is what the schools give", without == 2.0, without)
check("diffused printing makes the same schools teach faster", with_printing > without, (without, with_printing))
game, asked = schooling(0.0, 1.0)
check("with no school open printing teaches nobody", AdoptionMixin.effective_schooling_flow(game) == 0.0, None)
game, asked = schooling(2.0, 0.5)
AdoptionMixin.effective_schooling_flow(game, "literacy_general")
check("the figure asked about is passed to the schools that teach it", asked == ["literacy_general"], asked)

check("a concern's row names the foreman trade and his share of the year, rounded",
      specialist_foreman(SimpleNamespace(venture_foreman=lambda node_id: ("glassblower", 0.254)), "mirror") == {"trade": "glassblower", "fte": 0.25}, None)
check("a concern that needs no specialist names none", specialist_foreman(SimpleNamespace(venture_foreman=lambda node_id: (None, 0.0)), "plain") is None, None)
