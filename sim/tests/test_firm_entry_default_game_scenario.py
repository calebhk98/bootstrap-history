"""Scenario, Complaint 476: in a default game (nothing readied by a test helper) a concern the founder runs is in an entrant's sight and copyable.
An entrant sees a concern from where its country sits; a country sits where its people are, so the founder's
concern is in sight. Slow topic: it builds a game on the open agent economy and runs a few years.

Re-measure: `python3 -m sim.tests --slow --only firm_entry_default_game_scenario`."""
from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRecord, Firm, PLAYER_VISIBLE_EXPOSURE, imitation
from sim.engine.agents_port import SimWorld
from sim.geography.api import settlement, tiles_held

# a real concern an entrant earns by after its wages and site rent at the economy's price on the founder's tile, and
# that an entrant can copy once it is published; the others that earn at the opening are too hard to copy from sight
# (re-measure: for each node, `SimWorld.entry_gross` less the `business_books.yearly_costs`
# and `firm_entry.carrying_cost`, above zero, then found a firm here)
CONCERN = "lead_metallurgy"


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
	projects.business.set_opened_year(CONCERN, year - 10)
	game._done_changed()
	return game


game = default_game_with_founder_concern()
for _ in range(6):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)
# whether an entrant then finds the concern worth founding is the entry rules' own business (test_firm_entry_market*,
# which fix the cost of capital); here the game's placement must put the concern in sight and leave a chain to copy
probe = Firm("probe", ActorRecord(kind="firm", founded_year=game.state.scenario.year))
chain = imitation.missing_chain(CONCERN, SimWorld(game), probe)
check("an entrant at the home country can copy the founder's concern, in a default game", chain is not None, chain)

home = game.actors.actors["government:" + game.actors.state.home_country]
check("the home country sits where most of its people live",
      home.record.location == settlement.default_base_tile(tiles_held(game.civ)), home.record.location)
check("the founder's seat is within an entrant's sight of the home country",
      SimWorld(game).exposure(CONCERN, home.record.location) >= PLAYER_VISIBLE_EXPOSURE,
      SimWorld(game).exposure(CONCERN, home.record.location))
