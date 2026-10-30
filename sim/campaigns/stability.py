"""The year's stability phase: each state's grievances, hunger and liability burden become unrest on its tiles; where the
discontented, armed, would more likely than not beat the garrison they rise and fight it (the battle rule), and a won rising
takes the tile from the state or, at the seat, replaces the ruler. A disputed accession is settled the same way at the seat.

The rules are in `sim/agents/{unrest,revolt,authority,ruler}.py`, `sim/world/battle.py` and `rules.py`; this reads the tiles,
the armies and the state's books and writes the result back through the state's commands. Owners are taken in id order, tiles
in id order, so a year does not depend on the order things were created in a save."""
from typing import Any, Dict, List, Optional

from sim.agents.api import authority, collection, revolt, ruler, tax_burden, unrest
from sim.agents.api import government_levers_tax
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.polity.api import (CloseSuccessionDispute, RecordRising, RegisterPeople, ReplaceRuler, ResetStateUnrest,
                            SetGrievanceReference, SetLandTakenMemory, SetTileReading)
from sim.world import battle, campaign_contest
from sim.world.army_record import Army

from . import rules

RISINGS_KEPT = 20


class Stability:
	"""The phase `revolts`. Reads: civilisation, countries, has_state, country_world, organised_factions, food_eaten,
	year, tile_owner; the module's own garrisons and sites. Sends the state's commands (polity), TransferTile and
	RecordWorldEvent."""

	def stability_owners(self) -> List[str]:
		"""The countries with a state to be risen against: the home country, then the others in id order."""
		home = str(self.needs.civilisation()["id"])
		return [home] + sorted(owner for owner in self.needs.countries() if owner != home)

	def step_revolts(self, seats) -> None:
		for owner in self.stability_owners():
			if self.needs.has_state[owner]:
				self._stability_of(owner)

	# ---- readings of a state's year
	def _state_grievance(self, world: Any, record: Any) -> Optional[float]:
		income = sum(world.notice_over(scale) * income for scale, income in world.visible_taxpayers())
		return rules.state_grievance(income, float(world.pay_per_person_year("labourer")), float(world.hours_per_person_year),
		                             sum(record.corvee_hours.values()), sum(record.revenue_by_form.values()),
		                             record.need.get("dole", 0.0), record.unfunded.get("dole", 0.0), sum(record.unfunded.values()))

	def _faction_readings(self, owner: str, people: float):
		"""(people-weighted grievance, members) of the organised interest groups of the owner."""
		pairs = self.needs.organised_factions[owner]
		return unrest.faction_grievance(pairs, people), sum(members for members, _ in pairs)

	def _garrison_on(self, owner: str, tile: str) -> Optional[Army]:
		"""The owner's soldiers on a tile: its field armies there and the share of its free soldiers the tile's people bear."""
		field = sorted((Army.from_dict(record) for record in self.world.armies.values()
		                if record["owner"] == owner and record["tile"] == tile and record["soldiers"] >= 1.0),
		               key=lambda army: army.army_id)
		garrison = self._garrison(owner, tile, {})
		side = field + ([garrison] if garrison.soldiers > 0.0 else [])
		return campaign_contest.combine(side) if side else None

	def _stability_of(self, owner: str) -> None:
		world = self.needs.country_world[owner]
		record = world.government().record
		year = int(self.needs.year())
		people_by_tile = {tile: people for tile, people in sorted(world.collection_people_by_tile().items()) if people > 0.0}
		self.needs.send(SetLandTakenMemory(owner, unrest.fade_memory(record.land_taken_by_tile)))
		if not people_by_tile:
			return
		people = sum(people_by_tile.values())
		registered = {tile: max(record.registered_people.get(tile, 0.0), count) for tile, count in people_by_tile.items()}
		self.needs.send(RegisterPeople(owner, people_by_tile))
		state_grievance = self._state_grievance(world, record)
		faction_grievance, faction_members = self._faction_readings(owner, people)
		felt = faction_grievance
		if state_grievance is not None:
			grown_used_to = state_grievance if record.grievance_reference is None else record.grievance_reference
			felt += unrest.adapted(state_grievance, grown_used_to)
			self.needs.send(SetGrievanceReference(owner, unrest.adapt(grown_used_to, state_grievance)))
		rule = government_levers_tax.liability_rule(record)
		rate = tax_burden.harvest_share_taken(world)
		eaten = self.needs.food_eaten()
		reference = self._reference_equipment(owner)
		seat = collection.seat_tile(people_by_tile)
		self.needs.send(ResetStateUnrest(owner))
		for tile, count in people_by_tile.items():
			burden = unrest.liability_burden(rule, rate, registered[tile], count)
			share = unrest.unrest(felt + record.land_taken_by_tile.get(tile, 0.0), unrest.hunger(eaten.get(tile)), burden)
			soldiers = unrest.rising_soldiers(count, share, unrest.organisation(faction_members, people))
			garrison = self._garrison_on(owner, tile)
			site = self.campaign_site(tile)
			terrain = battle.terrain_factor(site.ruggedness, self.tile_fortification(tile))
			against = 0.0 if garrison is None else campaign_contest.strength_of(garrison, reference, terrain)
			strength = unrest.rising_strength(soldiers, reference)
			self.needs.send(SetTileReading(owner, tile, share, authority.hold(against, strength)))
			if unrest.rises(strength, against):
				self._rising(owner, world, record, tile, soldiers, strength, garrison, against, tile == seat, year, "unrest")
		if record.succession_challenger:
			self._disputed_accession(owner, world, record, seat, people_by_tile, faction_members, reference, year)

	# ---- a rising and what it changes
	def _rising(self, owner: str, world: Any, record: Any, tile: str, soldiers: float, strength: float,
	            garrison: Optional[Army], garrison_strength: float, on_seat: bool, year: int, cause: str) -> str:
		draw = world.rng_for("revolt", tile, year).random()
		result = revolt.resolve(soldiers, strength, 0.0 if garrison is None else garrison.soldiers, garrison_strength, on_seat, draw)
		self.needs.send(RecordWorldEvent("revolt", actors=(owner,), tiles=(tile,), cause=cause, facts=dict(
			outcome=result.kind, rising_win_probability=result.rising_win_probability, rising_lost=result.rising_lost,
			garrison_lost=result.garrison_lost)))
		self.needs.send(RecordRising(owner, {"year": year, "tile": tile, "kind": result.kind, "soldiers": round(soldiers)},
		                             RISINGS_KEPT))
		self.strike_from_force(owner, result.garrison_lost)
		if result.kind == revolt.TILE_LOST:
			self.needs.send(TransferTile(tile, None, "revolt"))
		elif result.kind == revolt.RULER_REPLACED:
			self.needs.send(ReplaceRuler(owner, ruler.opening_age(),
			                             "rising" if cause == "unrest" else record.succession_challenger))
		return result.kind

	def _disputed_accession(self, owner: str, world: Any, record: Any, seat: Optional[str], people_by_tile: Dict[str, float],
	                        faction_members: float, reference: float, year: int) -> None:
		"""The runner-up faction takes arms at the seat against the garrison there, in proportion to its backing."""
		challenger = record.succession_challenger
		backing = world.faction_backing()
		total = sum(backing.values())
		if seat is None or challenger not in backing or total <= 0.0:
			self.needs.send(CloseSuccessionDispute(owner))
			return
		soldiers = unrest.rising_soldiers(people_by_tile[seat], backing[challenger] / total)
		garrison = self._garrison_on(owner, seat)
		terrain = battle.terrain_factor(self.campaign_site(seat).ruggedness, self.tile_fortification(seat))
		against = 0.0 if garrison is None else campaign_contest.strength_of(garrison, reference, terrain)
		self._rising(owner, world, record, seat, soldiers, unrest.rising_strength(soldiers, reference), garrison, against,
		             True, year, "disputed_accession")
		self.needs.send(CloseSuccessionDispute(owner))
