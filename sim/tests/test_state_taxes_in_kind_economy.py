"""Complaint 622: in a running game a levy on a non-grain good reads what the home producers made of it last
year from the agent economy, in tonnes, and takes the rate of it into the state's stores. Complaint 640: the two
readings that carry the economy's record to the state (units to tonnes, the tiles the state holds) are called on
stand-ins built here; the levy, its price and its stores are held by test_state_taxes_in_kind."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.agents_port_revenue import RevenueView
from sim.engine.economy_port_year import AgentEconomy

GOOD = "cloth_kg"
UNITS_BY_TILE = {"a": {GOOD: 4000.0, "wheat_kg": 9000.0}, "b": {GOOD: 1000.0}, "far": {GOOD: 7000.0}}

port = SimpleNamespace(economy=lambda: SimpleNamespace(record=SimpleNamespace(output_by_tile=UNITS_BY_TILE)))
tonnes_by_tile = AgentEconomy.output_tonnes_by_tile(port)
check("the economy's units of a kilogram good are reported in tonnes, a thousand units to the tonne",
      abs(tonnes_by_tile["a"][GOOD] - 4.0) < 1e-12 and abs(tonnes_by_tile["b"][GOOD] - 1.0) < 1e-12, tonnes_by_tile)
check("every tile and good is kept", set(tonnes_by_tile) == set(UNITS_BY_TILE) and "wheat_kg" in tonnes_by_tile["a"], tonnes_by_tile)


class OutputView(RevenueView):
    """The revenue questions over a stand-in game that holds tiles a and b and answers tonnes by tile."""

    def __init__(self, by_tile):
        self._sim = SimpleNamespace(economy=SimpleNamespace(agent_output_tonnes_by_tile=lambda: by_tile))

    def held_tiles(self):
        return ["a", "b"]


view = OutputView(tonnes_by_tile)
check("the world reports what the held tiles made of a good, in tonnes, and not what other tiles made",
      abs(view.output_tonnes(GOOD) - 5.0) < 1e-12, view.output_tonnes(GOOD))
check("limited to a tile it reports only that tile's output", abs(view.output_tonnes(GOOD, frozenset({"b"})) - 1.0) < 1e-12)
check("a good nobody made is none", view.output_tonnes("silk_kg") == 0.0)
check("while the economy opens it answers nothing", OutputView({}).output_tonnes(GOOD) == 0.0)
