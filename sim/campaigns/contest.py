"""A siege and a storm, and a tile won: the army that stands on another owner's tile fights its defenders by the battle
rule; a tile won is held at the level the control data names and rises with the years it is held."""
from typing import Dict, List

from sim.actors.api import RecordConquestContact
from sim.geography.api import settlement, tile_owners
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.stores.api import WriteStore
from sim.world import campaign_contest, campaign_supply, campaign_year_rules
from sim.world.army_record import Army

RETREAT_NOTE = "withdrew"
CONTROL_STORE = "control"


class Contest:
	"""Reads: year, tile_owner, tiles_owned_by, tile_facts, country_world, store; sends TransferTile,
	RecordConquestContact, RecordWorldEvent, WriteStore."""

	def tile_fortification(self, tile: str) -> float:
		"""The strength works add to a defender on this tile. No works the model reads yet add any."""
		return 0.0

	def _garrison(self, defender: str, tile: str, armies: Dict[str, Army]) -> Army:
		"""The soldiers of the defending state not in an army, shared over its tiles by their people, as a force
		on the tile with the state's equipment and no food of its own: it eats the tile's stores."""
		owned = self.needs.tiles_owned_by[defender]
		share = settlement.population_share(owned, tile) if tile in owned else 0.0
		free = campaign_year_rules.garrison_strength(self.free_soldiers(defender), share)
		equipment = float(self.needs.country_world[defender].equipment_kg_per_soldier()) if self.needs.has_state[defender] else 0.0
		return Army("garrison", defender, tile, free, equipment)

	def _contest(self, army: Army, armies: Dict[str, Army], defender: str, days_left: float, modes: List[str],
	             pay_years: float, lost: Dict[str, float], reference: float) -> None:
		tile = army.tile
		field = sorted((other for other in armies.values() if other.owner == defender and other.tile == tile
		                and other.soldiers >= 1.0), key=lambda other: other.army_id)
		garrison = self._garrison(defender, tile, armies)
		side = field + ([garrison] if garrison.soldiers >= 1.0 else [])
		year = int(self.needs.year())
		rng = self.needs.country_world[army.owner].rng_for("battle", tile, army.army_id, year)
		site = self.campaign_site(tile)
		site.fortification = self.tile_fortification(tile)
		result = "defenders_gone" if not side else "continues"
		while side and days_left > 0.0:
			before = sum(member.soldiers for member in side)
			combined = campaign_contest.combine(side)
			turn_days = min(campaign_contest.SIEGE_TURN_DAYS, days_left)
			drawn_before = site.drawn_kcal
			per_day, source = self.campaign_column(army, modes)
			attacker_before = army.soldiers
			turn = campaign_contest.siege_turn(army, combined, site, per_day, reference, rng.random(), turn_days, pay_years)
			self._draw_down(tile, site.drawn_kcal - drawn_before)
			if source is not None and turn["carriage_taken_kg"] > 0.0:
				self._draw_down(source, campaign_supply.kcal_of(turn["carriage_taken_kg"]))
			campaign_contest.share_out(side, before, combined)
			lost[army.owner] = lost.get(army.owner, 0.0) + attacker_before - army.soldiers
			lost[defender] = lost.get(defender, 0.0) + before - sum(member.soldiers for member in side)
			days_left -= turn_days
			result = turn["result"]
			outcome = turn["outcome"]
			if outcome is not None:
				self.needs.send(RecordWorldEvent(
					"battle", actors=(army.owner, defender), tiles=(tile,), cause="assault",
					facts=dict(attacker_won=outcome.attacker_won, attacker_win_probability=outcome.attacker_win_probability,
					           attacker_lost=outcome.attacker_lost, defender_lost=outcome.defender_lost)))
				if outcome.attacker_won:   # captives of the defeated join the winner's bonded (648)
					self.take_captives_from_battle(army.owner, defender, outcome.defender_lost, tile)
				else:
					self.take_captives_from_battle(defender, army.owner, outcome.attacker_lost, tile)
			if result != "continues":
				break
		action = campaign_year_rules.contest_action(result)
		if action == "take":
			self._take(army, defender, armies)
		elif action == "withdraw":
			self._withdraw(army, result)
		for member in side:
			if member is not garrison and member.soldiers < 1.0:
				armies.pop(member.army_id, None)
		if action == "take":
			for member in field:
				if member.army_id in armies:
					self._rout(member, armies)

	def _take(self, army: Army, defender: str, armies: Dict[str, Army]) -> None:
		"""The army holds a tile whose defenders are gone: it passes to the army's owner at the level newly taken ground
		is held at, and the tile's people and taxes follow through the owner map."""
		tile = army.tile
		self.take_captives_from_conquest(army.owner, defender, tile)   # before the tile changes hands (648)
		previous = self.needs.send(TransferTile(tile, army.owner, "conquest", tile_owners.conquest_level(0.0)))
		self.world.held_since[tile] = campaign_year_rules.conquest_entry(int(self.needs.year()), army.owner, previous)
		army.log.append({"kind": "conquest", "tile": tile, "from": previous})
		self.needs.send(RecordConquestContact(army.owner, previous, tile))

	def _withdraw(self, army: Army, why: str) -> None:
		owned_home = bool(army.home_tile) and self.needs.tile_owner[army.home_tile] == army.owner
		campaign_year_rules.withdraw(army, why, owned_home, RETREAT_NOTE)

	def _rout(self, army: Army, armies: Dict[str, Army]) -> None:
		"""A defending army beaten on its own ground falls back to the tile it was raised at, if that is still its
		owner's and not this one, else its men go home and it is stood down."""
		owned_home = bool(army.home_tile) and self.needs.tile_owner[army.home_tile] == army.owner
		if campaign_year_rules.rout(army, owned_home):
			armies.pop(army.army_id, None)

	def _consolidate_conquests(self) -> None:
		"""A tile taken by an army rises in control the longer its owner holds it with an army on it."""
		held_since = self.world.held_since
		controls = self.needs.store[CONTROL_STORE]
		year = int(self.needs.year())
		levels = tile_owners.control_levels()
		for tile, entry in sorted(held_since.items()):
			garrisoned = any(record["owner"] == entry["by"] and record["tile"] == tile
			                 for record in self.world.armies.values())
			keep, level = campaign_year_rules.consolidation(entry, self.needs.tile_owner[tile], garrisoned, year,
			                                                controls["values"].get(tile, controls["default"]), levels,
			                                                tile_owners.conquest_level)
			if not keep:
				del held_since[tile]
			elif level is not None:
				self.needs.send(WriteStore(CONTROL_STORE, tile, level))
