"""Complaint 476: in a default game (nothing readied by a test helper) a firm enters a concern the founder runs.
An entrant sees a concern from where its country sits; a country sits where its people are, so the founder's
concern is in sight. Slow topic: it builds a game on the open agent economy and runs a few years.

Re-measure: `python3 -m sim.tests --slow --only firm_entry_default_game`."""
from .harness import *  # noqa: F401,F403

from sim.agents.api import PLAYER_VISIBLE_EXPOSURE
from sim.engine.agents_port import SimWorld
from sim.geography.api import settlement, tiles_held

# a real concern that pays in the opening economy (re-measure: scan the nodes for `SimWorld.concern_margin` above zero)
CONCERN = "pwr_coking"


def default_game_with_founder_concern():
	game = sim()
	year = game.state.scenario.year
	projects = game.state.projects
	projects.done.add(CONCERN)
	projects.done_year[CONCERN] = year - 10
	projects.operating.add(CONCERN)
	projects.opened_year[CONCERN] = year - 10
	game._done_changed()
	return game


game = default_game_with_founder_concern()
for _ in range(6):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)
copies = [firm for firm in game.actors.active_firms() if firm.record.target == CONCERN]
check("a firm enters a concern the founder runs, in a default game", len(copies) > 0, len(copies))

home = game.actors.actors["government:" + game.actors.state.home_country]
check("the home country sits where most of its people live",
      home.record.location == settlement.default_base_tile(tiles_held(game.civ)), home.record.location)
check("the founder's seat is within an entrant's sight of the home country",
      SimWorld(game).exposure(CONCERN, home.record.location) >= PLAYER_VISIBLE_EXPOSURE,
      SimWorld(game).exposure(CONCERN, home.record.location))
