"""The stability phase's per-tile arithmetic over arrays: unrest, the rising's arms, the garrison's strength, the hold and whether the
tile rises. The plain functions it reproduces bit for bit are `sim/agents/unrest.py`, `authority.py`, `liability.py` and
`sim/world/battle.py`; `sim/tests/stability_tiles_plain.py` keeps them chained for a test that runs both on random inputs.

A tile is a row: every column below is one float per tile, in the order the phase reads the tiles (id order)."""
import math

import numpy as np

from sim.jit import njit

# Columns of `TileInputs`: what the phase reads of each tile before the kernel runs.
TILE_COLUMNS = (
	"people",              # people living on the tile now (count of payers remaining)
	"registered",          # people the state has registered on the tile (never fewer than `people`)
	"land_taken",          # grievance still felt over land taken from the tile's holders (share of income)
	"eaten_over_need",     # share of the tile's food need the economy booked as eaten; NaN when no food is booked for the tile
	"garrison_soldiers",   # soldiers on the tile on the state's side: field armies there and its share of the free soldiers
	"garrison_equipment",  # their equipment, kg of worked iron and ammunition per soldier per year (head-weighted)
	"garrison_supply",     # their supply state, 0 to 1 (head-weighted)
	"ruggedness",          # the tile's ruggedness
	"fortification",       # the strength works on the tile add to a defender
)


@njit
def equipment_quality(equipment_kg, reference_kg, exponent):
	"""Fighting quality of a soldier supplied with `equipment_kg`, against the reference soldier's (`battle.equipment_quality`)."""
	return (max(0.0, equipment_kg) / reference_kg) ** exponent


@njit
def win_probability(attacker, defender, decisiveness):
	"""The attacker's chance of beating the defender (`battle.attacker_win_probability`)."""
	if attacker <= 0.0:
		return 0.0
	if defender <= 0.0:
		return 1.0
	weight = attacker ** decisiveness
	return weight / (weight + defender ** decisiveness)


@njit
def liability_burden(collective, rate, registered, remaining):
	"""How much heavier a stayer's take is under a collective rule than under an individual one, 0 when equal or when nobody
	remains (`unrest.liability_burden` with no remission)."""
	if remaining <= 0.0:
		return 0.0
	own = max(0.0, rate) * (1.0 - 0.0)
	individual = min(1.0, own)
	held = individual
	if collective:
		held = min(1.0, own * max(registered, remaining) / remaining)
	if individual <= 0.0:
		return 0.0
	return max(0.0, held / individual - 1.0)


@njit
def read_tiles(people, registered, land_taken, eaten_over_need, garrison_soldiers, garrison_equipment, garrison_supply,
               ruggedness, fortification, felt, collective, rate, organised, reference_kg, constants):
	"""One pass over the tiles: (unrest share, rising soldiers, rising strength, garrison strength, hold, rises) per tile.

	`felt` is the grievance the whole state's people feel, `collective` whether the state's liability rule is collective, `rate`
	the harvest share it takes, `organised` the share of the discontented who act together, `reference_kg` the reference soldier's
	equipment. `constants` holds, in this order: armed share of the discontented, the rising's equipment share of the reference,
	equipment quality exponent, battle decisiveness, terrain defence maximum, ruggedness half effect."""
	armed_share = constants[0]
	rising_equipment_share = constants[1]
	quality_exponent = constants[2]
	decisiveness = constants[3]
	terrain_maximum = constants[4]
	rugged_half = constants[5]
	count = people.shape[0]
	share = np.empty(count)
	soldiers = np.empty(count)
	strength = np.empty(count)
	against = np.empty(count)
	hold = np.empty(count)
	rises = np.zeros(count, dtype=np.int8)
	rising_quality = equipment_quality(rising_equipment_share * reference_kg, reference_kg, quality_exponent)
	for tile in range(count):
		burden = liability_burden(collective, rate, registered[tile], people[tile])
		hunger = 0.0
		if not math.isnan(eaten_over_need[tile]):
			hunger = max(0.0, min(1.0, 1.0 - eaten_over_need[tile]))
		pressure = max(0.0, felt + land_taken[tile]) + max(0.0, hunger) + max(0.0, burden)
		share[tile] = 1.0 - math.exp(-pressure)
		soldiers[tile] = (max(0.0, people[tile]) * max(0.0, min(1.0, share[tile])) * armed_share
		                  * max(0.0, min(1.0, organised)))
		strength[tile] = max(0.0, soldiers[tile]) * rising_quality * max(0.0, min(1.0, 1.0)) * max(0.0, 1.0)
		if garrison_soldiers[tile] > 0.0:
			rugged = max(0.0, ruggedness[tile])
			terrain = (1.0 + terrain_maximum * rugged / (rugged + rugged_half)) * (1.0 + max(0.0, fortification[tile]))
			against[tile] = (max(0.0, garrison_soldiers[tile])
			                 * equipment_quality(garrison_equipment[tile], reference_kg, quality_exponent)
			                 * max(0.0, min(1.0, garrison_supply[tile])) * max(0.0, terrain))
		else:
			against[tile] = 0.0
		if strength[tile] <= 0.0:
			hold[tile] = 1.0
		else:
			hold[tile] = 1.0 - win_probability(strength[tile], max(0.0, against[tile]), decisiveness)
		if strength[tile] > 0.0 and win_probability(strength[tile], against[tile], decisiveness) >= 0.5:
			rises[tile] = 1
	return share, soldiers, strength, against, hold, rises
