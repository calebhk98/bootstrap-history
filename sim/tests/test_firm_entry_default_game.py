"""Complaint 476: in a default game (nothing readied by a test helper) a firm enters a concern the founder runs.
An entrant sees a concern from where its country sits; a country sits where its people are, so the founder's
concern is in sight. Slow topic: it builds a game on the open agent economy and runs a few years.

Re-measure: `python3 -m sim.tests --slow --only firm_entry_default_game`."""
from .harness import *  # noqa: F401,F403

from sim.agents.api import PLAYER_VISIBLE_EXPOSURE
from sim.engine.agents_port import SimWorld
from sim.geography.api import settlement, tiles_held

# a real concern an entrant earns by after its wages and site rent at the economy's price on the founder's tile, and
# that an entrant can copy once it is published; the others that earn at the opening are too hard to copy from sight
# (re-measure: for each node, `SimWorld.entry_gross` less the `business_books.yearly_costs`
# and `firm_entry.carrying_cost`, above zero, then found a firm here)
CONCERN = "finery_puddling"


def add_with_prerequisites(game, node_id, found):
	if node_id in found:
		return
	found.add(node_id)
	for prerequisite in game.nodes[node_id].get("pre") or ():
		add_with_prerequisites(game, prerequisite, found)


def default_game_with_founder_concern():
	game = sim()
	year = game.state.scenario.year
	projects = game.state.projects
	known = set()
	add_with_prerequisites(game, CONCERN, known)   # a founder who runs a concern holds what it stands on
	for node_id in known:
		projects.done.add(node_id)
		projects.done_year[node_id] = year - 10
	projects.disclosures[CONCERN] = {"mode": "publish"}   # an entrant copies only what it can see
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
