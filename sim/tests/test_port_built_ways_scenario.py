"""Scenario (Complaint 416): the ways a game has built (`state.economy.improvements`) reach the agent economy through the
port: the setup carries them, the opening prices a road, and the live economy is given them when a way is finished.
The carriage-table, setup and spin-up-key rules are in test_economy_built_ways."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup
from sim.geography import api as geography_api

game = sim()
setup = economy_port_setup.build_setup(game)
check("a game with nothing built hands the economy no ways", setup.improvements == {}, setup.improvements)

carriage = economy_port_setup.opening_values(game)["carriage"]
check("a built road is priced as carriage, cheaper per tonne-km than a track",
      "road" in carriage and 0.0 < carriage["road"] < carriage["cart"], carriage)

tiles = sorted(setup.tiles)
pair = next((tile, other) for tile in tiles for other in setup.tiles[tile].borders if other in setup.tiles)
edge = geography_api.edge_key(*pair)

game.state.economy.improvements = {edge: {"road": True}}
built = economy_port_setup.build_setup(game)
check("the setup carries the game's built ways", built.improvements == {edge: {"road": True}}, built.improvements)

game.state.economy.improvements = {}
economy = game.economy.agent.economy()
live_before = economy.carriage.cost_per_tonne(*pair)
game.state.economy.improvements = {edge: {"road": True}}
game.economy.agent.sync_ways()
check("a way finished mid-game rebuilds the live carriage table", economy.carriage.cost_per_tonne(*pair) < live_before)
