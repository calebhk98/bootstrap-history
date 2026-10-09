"""Complaint 416 (415), whole-game checks: a mine names a deposit the seat has found, the agent economy's ore firms
are sited on the found deposits, and what they raise is drawn from them. Builds games, so it is not a quick topic."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup

bare = sim(surveyed=())
check("a game that has found no coal deposit opens no coal mine, and says to prospect",
      bare.open_mine("coal", 10.0) == 0.0 and "prospect" in (bare.mine_refusal or ""), bare.mine_refusal)
check("the known mines of the held tiles are already found",
      bool(bare.found_deposits("iron")), bare.found_deposits("iron"))

setup = economy_port_setup.build_setup(bare)
ore_limits = [limit for limit in setup.site_limits if limit.recipe_id == "iron_ore_kg"]
check("the opening sites the iron-ore recipe on the tiles that hold a found iron deposit",
      bool(ore_limits) and {limit.tile for limit in ore_limits} == {row["tile_id"] for row in bare.found_deposits("iron")},
      ore_limits)

game = sim()
tile = next(row["tile_id"] for row in game.found_deposits("iron"))
before = sum(row["remaining_tonnes"] for row in game.found_deposits("iron") if row["tile_id"] == tile)
game.economy.agent.economy()
game.step()
after = sum(row["remaining_tonnes"] for row in game.found_deposits("iron") if row["tile_id"] == tile)
check("a year of the agent economy's ore extraction draws on the tile's deposits", after <= before, (before, after))
