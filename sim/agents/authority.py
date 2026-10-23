"""What a state can do on a tile: reach from the officials and the road, hold from the garrison against a rising, and the
share officials keep.

    reach_of_tile  = collection share of the tile (officials, their time and the road from the seat: collection.py)
    hold_of_tile   = 1 - chance a rising of the tile's discontented beats the garrison on it (battle.py)
    authority      = reach_of_tile * hold_of_tile
    share_kept     = KEEP_CEILING * (1 - exp(-travel_days / KEEP_DISTANCE_SCALE_DAYS)) * (1 - oversight)

Collection, order and conscription on a tile each scale by its authority; what officials keep is never booked as the state's
revenue. Plain functions of numbers: the engine reads the tile and hands them in."""
import math
from typing import Any, Iterable, Mapping, Optional

from sim.constants import declare
from sim.world import battle

OFFICIAL_KEEP_CEILING = declare(
	"OFFICIAL_KEEP_CEILING", 0.4, kind="temporary_heuristic",
	unit="share of what is collected", source=None, confidence="D",
	retire="Complaints/484: officials as actors with their own pay, purse and bribes",
	why="The most of what they collect officials keep when the tile is far and no one checks them. No source "
		"opened gives a share for a pre-modern state; stands in for officials' own ledgers.")
OFFICIAL_KEEP_DISTANCE_SCALE_DAYS = declare(
	"OFFICIAL_KEEP_DISTANCE_SCALE_DAYS", 20.0, kind="temporary_heuristic",
	unit="days of travel from the seat", source=None, confidence="D",
	retire="Complaints/484: officials as actors with their own pay, purse and bribes",
	why="Days of travel at which an unwatched official keeps about two thirds of the ceiling: the farther from the "
		"seat, the longer a report takes to come back and the cheaper it is to keep a share.")


def hold(garrison_strength: float, rising_strength: float) -> float:
	"""Share of risings the garrison would put down: one minus the attacker's win chance in `battle`, given the two
	effective strengths. A tile with no one in arms against the state is held whatever the garrison; a rising against no
	garrison wins."""
	if rising_strength <= 0.0:
		return 1.0
	return 1.0 - battle.attacker_win_probability(rising_strength, max(0.0, garrison_strength))


def authority(reach: float, held: float) -> float:
	"""What the state can collect, order and conscript on a tile, 0 to 1."""
	return max(0.0, min(1.0, reach)) * max(0.0, min(1.0, held))


def share_kept(travel_days: Optional[float], oversight: float) -> float:
	"""Share of its collections the officials of a tile keep: rises with the days of road to the seat, falls with the
	share of their workings the state's inspectors check. A tile no road reaches (None) is kept at the ceiling."""
	distance = 1.0 if travel_days is None else 1.0 - math.exp(-max(0.0, travel_days) / OFFICIAL_KEEP_DISTANCE_SCALE_DAYS)
	return OFFICIAL_KEEP_CEILING * distance * (1.0 - max(0.0, min(1.0, oversight)))


def people_weighted_kept(people_by_tile: Mapping[str, float], days_by_tile: Mapping[str, float],
						 oversight_by_tile: Mapping[str, float], tiles: Optional[Iterable[str]] = None) -> float:
	"""`share_kept` weighted by the people on `tiles` (all when none) that the state's officials can reach by road."""
	chosen = list(people_by_tile) if tiles is None else [tile for tile in tiles if tile in people_by_tile]
	reached = [tile for tile in chosen if tile in days_by_tile]
	people = sum(people_by_tile[tile] for tile in reached)
	if people <= 0.0:
		return 0.0
	return sum(people_by_tile[tile] * share_kept(days_by_tile[tile], oversight_by_tile.get(tile, 0.0))
			   for tile in reached) / people


def conscripts(people: float, levy_share: float, tile_authority: float) -> float:
	"""Soldiers a tile gives for a levy of `levy_share` of its people: only as many as the state's authority there compels."""
	return max(0.0, people) * max(0.0, min(1.0, levy_share)) * max(0.0, min(1.0, tile_authority))


def after_leakage(amount: float, kept: float) -> float:
	"""What reaches the state of `amount` collected when officials keep the share `kept`."""
	return amount * (1.0 - max(0.0, min(1.0, kept)))


def levy_reach(world: Any) -> float:
	"""The share of a levy the state can compel across what it holds: its collection reach, held by its garrisons; a world
	that reads none compels all."""
	reading = getattr(world, "collectible_share", None)
	return 1.0 if reading is None else float(reading(None))


def kept_on(world: Any, tiles: Optional[Iterable[str]]) -> float:
	"""The share officials keep over `tiles`, as the world reads it; none for a world that keeps no such reading."""
	reading = getattr(world, "corruption_share", None)
	return 0.0 if reading is None else float(reading(tiles))
