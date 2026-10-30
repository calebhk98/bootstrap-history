"""Armies in the game: where they are kept, who owns them, and what raising, ordering, recalling and disbanding one is.

The armies of every actor are records in the module's state ({army id: Army as a dict}). An owner is any actor that
owns tiles; its soldiers are the force its state keeps (the army line), an army being a slice of them. A seat that plays
a country raises armies for that country."""
from typing import Any, Dict, List, Optional

from sim.agents.api import army_raising
from sim.geography.api import settlement
from sim.polity.api import StrikeFromForce
from sim.refusal import Refusal
from sim.world import campaign_supply
from sim.world.army_record import Army, fielded_soldiers

from . import rules
from .commands import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy

ARMIES = "armies"


class Armies:
	"""Reads: tile_owner, tiles_owned_by, tile_facts, has_state, country_world, year. Sends StrikeFromForce."""

	def army_records(self) -> Dict[str, Dict[str, Any]]:
		return self.world.armies

	def save_army(self, army: Army) -> None:
		self.world.armies[army.army_id] = army.to_dict()
		self.bump(ARMIES)

	def army_of(self, army_id: str) -> Optional[Army]:
		record = self.world.armies.get(army_id)
		return None if record is None else Army.from_dict(record)

	def armies_of(self, owner: str) -> List[Army]:
		return [Army.from_dict(record) for _, record in sorted(self.world.armies.items()) if record["owner"] == owner]

	def owner_force(self, owner: str) -> float:
		"""Soldiers the owner's state keeps now."""
		return float(self.needs.country_world[owner].soldiers_under_arms()) if self.needs.has_state[owner] else 0.0

	def free_soldiers(self, owner: str) -> float:
		return army_raising.available_soldiers(self.owner_force(owner), fielded_soldiers(self.world.armies, owner))

	def strike_from_force(self, owner: str, killed: float) -> None:
		"""Take soldiers who died in the field off the owner's army line."""
		if killed <= 0.0 or not self.needs.has_state[owner]:
			return
		self.needs.send(StrikeFromForce(owner, killed))

	def armies_of_owner(self, owner: str) -> Dict[str, Any]:
		"""The view `armies`: the owner's armies and the soldiers of its force not in any."""
		return {"armies": self.armies_of(owner), "free_soldiers": self.free_soldiers(owner)}

	def raise_army(self, owner: str, soldiers: Any, tile: Optional[str] = None) -> Any:
		"""Raise an army of `soldiers` of the owner's force on one of its tiles (the best-endowed one when none is named);
		the new `Army`, or a Refusal."""
		owned = self.needs.tiles_owned_by[owner]
		tile = tile or (settlement.default_base_tile(owned) if owned else None)
		refusal = army_raising.raise_refusal(soldiers, self.free_soldiers(owner), self.needs.tile_owner[tile] if tile else None,
		                                     owner, self.needs.tile_facts[tile] is not None if tile else False)
		if refusal is not None:
			return refusal
		army_id = rules.army_id(self.world.next_id)
		self.world.next_id += 1
		world = self.needs.country_world[owner]
		army = Army(army_id, owner, tile, float(soldiers), float(world.equipment_kg_per_soldier()),
		            animals=float(soldiers) * campaign_supply.TRAIN_ANIMALS_PER_SOLDIER, home_tile=tile,
		            raised_year=int(self.needs.year()))
		self.save_army(army)
		return army

	def order_army(self, owner: str, army_id: Any, tile: Any) -> Any:
		"""Send an army to a tile; it marches from the next year's campaign (or this year's, if the year has not run)."""
		army = rules.own_army(self.world.armies, owner, army_id)
		if isinstance(army, Refusal):
			return army
		if not isinstance(tile, str) or self.needs.tile_facts[tile] is None:
			return Refusal("unknown_tile", "no such tile on the map. Nothing was changed.")
		rules.order(army, tile)
		self.save_army(army)
		return army

	def recall_army(self, owner: str, army_id: Any) -> Any:
		"""Order an army back to the tile it was raised on, or to the owner's best-endowed tile if that is no longer
		the owner's."""
		army = rules.own_army(self.world.armies, owner, army_id)
		if isinstance(army, Refusal):
			return army
		home = rules.recall_tile(army.home_tile, self.needs.tile_owner[army.home_tile], owner, self.needs.tiles_owned_by[owner])
		if home is None:
			return Refusal("no_tile_to_return_to", "the owner holds no tile to recall the army to. Nothing was changed.")
		return self.order_army(owner, army_id, home)

	def disband_army(self, owner: str, army_id: Any) -> Any:
		"""Stand an army down: its soldiers go back to the state's force, its food and animals are dispersed."""
		army = rules.own_army(self.world.armies, owner, army_id)
		if isinstance(army, Refusal):
			return army
		del self.world.armies[army_id]
		self.bump(ARMIES)
		return army

	def apply_raise_army(self, command: RaiseArmy) -> Any:
		return self.raise_army(command.owner, command.soldiers, command.tile)

	def apply_order_army(self, command: OrderArmy) -> Any:
		return self.order_army(command.owner, command.army_id, command.tile)

	def apply_recall_army(self, command: RecallArmy) -> Any:
		return self.recall_army(command.owner, command.army_id)

	def apply_disband_army(self, command: DisbandArmy) -> Any:
		return self.disband_army(command.owner, command.army_id)
