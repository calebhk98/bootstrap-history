"""What an armed rising does when it fights the state's garrison on a tile: the battle rule of `battle.py` with the
rising as attacker, and what the result changes.

    rising wins on the seat tile      -> the ruler is replaced (`RULER_REPLACED`)
    rising wins on any other tile     -> the tile leaves the state (`TILE_LOST`), held by no actor
    garrison wins                     -> the rising is put down (`PUT_DOWN`), and the dead come off both sides

A plain function of numbers; the engine reads the tile, hands in the strengths and a seeded draw, and applies the result
(transfer of the tile, a new ruler, soldiers struck from the force)."""
from typing import NamedTuple

from sim.world import battle

PUT_DOWN = "put_down"
TILE_LOST = "tile_lost"
RULER_REPLACED = "ruler_replaced"


class Result(NamedTuple):
	kind: str
	rising_won: bool
	rising_win_probability: float
	rising_lost: float
	garrison_lost: float


def resolve(rising_soldiers: float, rising_strength: float, garrison_soldiers: float, garrison_strength: float,
			on_seat: bool, draw: float) -> Result:
	"""One rising against one garrison. `draw` is a uniform number in [0, 1) from the caller's seeded stream."""
	fought = battle.fight(rising_strength, garrison_strength, rising_soldiers, garrison_soldiers, draw)
	kind = PUT_DOWN if not fought.attacker_won else (RULER_REPLACED if on_seat else TILE_LOST)
	return Result(kind, fought.attacker_won, fought.attacker_win_probability, fought.attacker_lost, fought.defender_lost)
