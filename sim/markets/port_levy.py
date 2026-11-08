"""The working time a state takes from its people, handed to the agent economy each year."""
import math


def levy_hours_per_worker(sim) -> float:
	"""Hours of each working person's year the home state called up for its works and its army this year (its record of
	hours taken), spread over the labour core's own workers on the tiles that nation holds; zero before the state has
	acted or while the core has no workers there. Partner tiles do not carry it."""
	government = sim.scenario.actors.countries.government_of(None)
	economy = sim.economy
	by_tile = None if economy.opening else economy.parts.producers.people_by_tile_and_trade()
	if government is None or not by_tile:
		return 0.0
	tiles = sim.labour.settlement_tiles()
	working_people = getattr(by_tile, "working_people", None)     # the core's people by tile read in one block; a plain mapping is summed tile by tile
	workers = working_people(tiles) if working_people else math.fsum(math.fsum(by_tile.get(tile, {}).values()) for tile in tiles)
	return max(0.0, government.corvee.corvee_hours_taken() / workers) if workers > 0.0 else 0.0
