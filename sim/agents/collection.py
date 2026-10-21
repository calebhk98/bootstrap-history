"""What a state can collect where: the officials it employs, their time, and the days it takes to reach each tile.

An official has a working year. Part of it goes on the road to a tile and back, each round of collection; the rest
is spent entering, checking and receiving what the people on the tile owe. Officials are spread over the tiles in
proportion to the time each tile asks (its people times the time one person's dues take, plus the road); where the
time falls short, a tile is collected in the share of its people the time reaches, and a far tile loses more of
its time to the road than a near one. Writing shortens the work of keeping rolls, so literate officials handle more.

    days_asked_by_tile = people_on_tile * days_per_person + rounds * 2 * travel_days_to_tile
    share_of_time = min(1, officials * working_days / sum of days_asked_by_tile)
    collectible_share_of_tile = min(1, (share_of_time * days_asked_by_tile - rounds * 2 * travel_days) / (people * days_per_person))

Nothing here reads a typed capacity: the officials come from the administration line the state pays, the time from
the working year, the reach from the route search (sim/geography/routes_search.py `reach`).
"""
from typing import Dict, Iterable, List, Mapping, Optional

from sim.constants import declare

ASSESSMENT_DAYS_PER_PERSON = declare(
	"ASSESSMENT_DAYS_PER_PERSON", 0.02, kind="temporary_heuristic",
	unit="official-days per person per round of collection (rolls kept without writing)", source=None, confidence="D",
	retire="Complaint 620 follow-up: collection time derived from the census and receipt records an administration keeps",
	why="The time an official needs to enter, check and receive one person's dues in a round when rolls are kept by "
		"memory and tally. No source found that gives it for a pre-modern state; stands in for a model of the work.")
WRITING_SAVES_SHARE_OF_ASSESSMENT = declare(
	"WRITING_SAVES_SHARE_OF_ASSESSMENT", 0.5, kind="temporary_heuristic",
	unit="share of assessment time saved at full literacy of the officials", source=None, confidence="D",
	retire="Complaint 620 follow-up: collection time derived from the census and receipt records an administration keeps",
	why="How much of an official's assessment time written rolls and receipts save when every official and clerk "
		"reads and writes. No source found; the saving is taken as linear in the officials' literacy.")
ROUNDS_OF_COLLECTION_PER_YEAR = declare(
	"ROUNDS_OF_COLLECTION_PER_YEAR", 1.0, kind="temporary_heuristic",
	unit="visits per tile per year", source=None, confidence="D",
	retire="Complaint 620 follow-up: rounds set by when the base is due (harvest, market days)",
	why="How often an official travels to a tile to collect, out and back; one round at the harvest stands in for "
		"the dates each base falls due.")


def days_per_person(literacy: float) -> float:
	"""Official-days one person's dues take in a round, less what writing saves."""
	return ASSESSMENT_DAYS_PER_PERSON * (1.0 - WRITING_SAVES_SHARE_OF_ASSESSMENT * min(1.0, max(0.0, literacy)))


def tile_shares(officials: float, working_days: float, literacy: float, people_by_tile: Mapping[str, float],
				travel_days_by_tile: Mapping[str, float]) -> Dict[str, float]:
	"""{tile: share of what is due there that the state's officials collect}. A tile with no road from the seat
	(absent from `travel_days_by_tile`) is collected in no share."""
	per_person = days_per_person(literacy)
	road = {tile: ROUNDS_OF_COLLECTION_PER_YEAR * 2.0 * travel_days_by_tile[tile]
			for tile in people_by_tile if tile in travel_days_by_tile}
	asked = {tile: people_by_tile[tile] * per_person + road[tile] for tile in road}
	total_asked = sum(asked.values())
	supply = max(0.0, officials) * max(0.0, working_days)
	time_share = 1.0 if total_asked <= 0.0 else min(1.0, supply / total_asked)
	shares = {tile: 0.0 for tile in people_by_tile}
	for tile, days in asked.items():
		work = people_by_tile[tile] * per_person
		shares[tile] = 1.0 if work <= 0.0 else min(1.0, max(0.0, time_share * days - road[tile]) / work)
	return shares


def collectible_share(shares: Mapping[str, float], people_by_tile: Mapping[str, float],
					  tiles: Optional[Iterable[str]] = None) -> float:
	"""The people-weighted share collected over `tiles` (all the tiles given when none)."""
	chosen: List[str] = list(people_by_tile) if tiles is None else [tile for tile in tiles if tile in people_by_tile]
	people = sum(people_by_tile[tile] for tile in chosen)
	if people <= 0.0:
		return 1.0 if not chosen else 0.0
	return sum(people_by_tile[tile] * shares.get(tile, 0.0) for tile in chosen) / people


def spread_people(total: float, shares: Mapping[str, float]) -> Dict[str, float]:
	"""`total` people over the tiles by `shares`; evenly where no tile is given any share (none settles a tile
	the settlement model finds empty, yet the people live somewhere)."""
	weight = sum(shares.values())
	if weight <= 0.0:
		return {tile: total / len(shares) for tile in shares}
	return {tile: total * share / weight for tile, share in shares.items()}


def seat_tile(people_by_tile: Mapping[str, float]) -> Optional[str]:
	"""Where the state sits: the tile with the most people (ties by id)."""
	return min(people_by_tile, key=lambda tile: (-people_by_tile[tile], tile)) if people_by_tile else None


def officials_employed(officials_kept: float, administration_need: float, administration_unfunded: float) -> float:
	"""The officials the state keeps less the share of their pay it could not meet."""
	if administration_need <= 0.0:
		return max(0.0, officials_kept)
	return max(0.0, officials_kept) * max(0.0, 1.0 - administration_unfunded / administration_need)
