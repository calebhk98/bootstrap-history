"""The stability phase over a whole state's tiles: read what the kernel needs of each tile into columns, run it once, and hand back
the rows. A rising changes what later tiles read (the garrison, the owner's tiles), so the phase asks for a fresh pass from the
tile after each rising; a quiet year is one pass."""
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from sim.agents.api import unrest
from sim.geography.api import settlement
from sim.world import battle, campaign_contest
from sim.world.army_record import Army

from . import stability_kernels


def kernel_constants() -> np.ndarray:
	"""The declared figures the kernel takes as one array, in the order `stability_kernels.read_tiles` documents."""
	return np.array([unrest.ARMED_SHARE_OF_DISCONTENTED, unrest.RISING_EQUIPMENT_SHARE_OF_REFERENCE,
	                 battle.EQUIPMENT_QUALITY_EXPONENT, battle.BATTLE_DECISIVENESS, battle.TERRAIN_DEFENCE_MAX,
	                 battle.RUGGEDNESS_HALF_EFFECT])


def field_armies_by_tile(armies: Dict[str, Dict[str, Any]], owner: str) -> Dict[str, List[Army]]:
	"""The owner's armies of one or more soldiers in the field, by tile, each tile's in army id order."""
	by_tile: Dict[str, List[Army]] = {}
	for record in armies.values():
		if record["owner"] == owner and record["soldiers"] >= 1.0:
			by_tile.setdefault(record["tile"], []).append(Army.from_dict(record))
	for field in by_tile.values():
		field.sort(key=lambda army: army.army_id)
	return by_tile


def garrison_columns(tiles: Sequence[str], owned: List[str], free_soldiers: float, equipment_kg: float,
                     field_by_tile: Dict[str, List[Army]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
	"""(soldiers, equipment kg, supply state) of the state's side on each tile: the field armies there combined with the garrison,
	the free soldiers shared over the owner's tiles by their people. A side with no soldiers has none of all three."""
	shares = settlement.population_shares(owned) if owned else {}
	share = np.array([shares.get(tile, 0.0) for tile in tiles])
	soldiers = free_soldiers * share
	has_garrison = soldiers > 0.0
	with np.errstate(invalid="ignore", divide="ignore"):
		equipment = np.where(has_garrison, (equipment_kg * soldiers) / soldiers, 0.0)
		supply = np.where(has_garrison, (1.0 * soldiers) / soldiers, 0.0)
	for position, tile in enumerate(tiles):
		field = field_by_tile.get(tile)
		if field:
			garrison = Army("garrison", field[0].owner, tile, float(soldiers[position]), equipment_kg)
			side = field + ([garrison] if garrison.soldiers > 0.0 else [])
			combined = campaign_contest.combine(side)
			soldiers[position], equipment[position], supply[position] = combined.soldiers, combined.equipment_kg, combined.supply_state
	return soldiers, equipment, supply


def read_tiles(columns: Dict[str, np.ndarray], felt: float, collective: bool, rate: float, organised: float,
               reference_kg: float) -> Tuple[np.ndarray, ...]:
	"""One kernel pass over the columns; the reference equipment must be positive, as `battle.equipment_quality` requires."""
	if reference_kg <= 0.0:
		raise ValueError("the reference equipment burden must be positive: %r" % (reference_kg,))
	return stability_kernels.read_tiles(*(columns[name] for name in stability_kernels.TILE_COLUMNS), felt, collective, rate,
	                                    organised, reference_kg, kernel_constants())
