"""The year's campaign phase: every army marches on its order, eats from what it carries and the land, wears down,
and where it stands on another actor's tile it besieges and storms it.

The rules are in `sim/world/campaign_*.py` and `battle.py`; this reads the tiles, the routes and the owners and
writes the result back. Armies are taken in id order, so a year does not depend on the order they were raised in
a save. A fight and a tile taken are in `contest.py`."""
from typing import Dict, List

from sim.agents.api import army_raising
from sim.world import campaign_contest, campaign_supply, campaign_year_rules, military_logistics
from sim.world.army_record import Army

from . import rules
from .armies import ARMIES


class CampaignYear:
	"""The phase `campaigns`. Reads: civilisation, home_modes, country_world, route_between, reach_from, tile_owner,
	tile_owner_map, tile_facts, played_countries, has_state; the module's own armies and captives."""

	# ---- readings of a tile
	def campaign_site(self, tile: str) -> campaign_contest.Site:
		facts = self.needs.tile_facts[tile]
		return campaign_contest.Site(tile, facts["food_kcal_per_year"], self.world.drawn.get(tile, 0.0),
		                             facts["working_age_endemic_loss"], facts["ruggedness"])

	def _draw_down(self, tile: str, kcal: float) -> None:
		drawn = self.world.drawn
		drawn[tile] = drawn.get(tile, 0.0) + kcal

	def campaign_modes(self, owner: str) -> List[str]:
		if owner == str(self.needs.civilisation()["id"]):
			return list(self.needs.home_modes())
		return list(self.needs.country_world[owner].collection_modes())

	def campaign_column(self, army: Army, modes: List[str]) -> tuple:
		"""(kg of grain a day the army's column brings, tile it comes from): the nearest tile of the owner's within the
		column's reach that still has grain to take."""
		days_to = self.needs.reach_from(army.tile, modes, campaign_supply.carriage_range_days())
		for tile, days in sorted(days_to.items(), key=lambda item: (item[1], item[0])):
			if self.needs.tile_owner[tile] != army.owner:
				continue
			site = self.campaign_site(tile)
			if campaign_supply.tile_stock_kg(site.food_kcal_per_year, site.drawn_kcal) > 0.0:
				return campaign_supply.carriage_kg_per_day(army.animals, days), tile
		return 0.0, None

	def _camp(self, army: Army, days: float, modes: List[str], pay_years: float, lost: Dict[str, float]) -> None:
		"""Spend `days` on the army's tile: the column's grain, the land's, then losses."""
		site = self.campaign_site(army.tile)
		per_day, source = self.campaign_column(army, modes)
		before = site.drawn_kcal
		result = campaign_contest.camp(army, days, site, per_day, pay_years)
		self._draw_down(army.tile, site.drawn_kcal - before)
		if source is not None and result["taken_carriage_kg"] > 0.0:
			self._draw_down(source, campaign_supply.kcal_of(result["taken_carriage_kg"]))
		campaign_year_rules.book_losses(army, result, lost)

	def _pay_years(self, army: Army) -> float:
		world = self.needs.country_world[army.owner]
		record = world.government().record
		owed = army_raising.pay_owed_share(record.arrears.get("army", 0.0), self.owner_force(army.owner), army.soldiers)
		army.pay_owed = owed
		return army_raising.pay_owed_years(owed, army.soldiers, float(world.pay_per_person_year("soldier")))

	def _reference_equipment(self, owner: str) -> float:
		"""The equipment burden of the reference soldier, whose quality is 1: the plain iron kit of the logistics model."""
		return military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()

	# ---- the phase
	def step_campaigns(self, seats) -> None:
		self.world.drawn = {}
		if not self.world.armies:
			return
		armies = {army_id: Army.from_dict(record) for army_id, record in sorted(self.world.armies.items())}
		for army in armies.values():
			army.log = []
		self._defend(armies)
		lost: Dict[str, float] = {}
		references: Dict[str, float] = {}
		for army_id in sorted(armies):
			if army_id in armies:
				self._campaign_army(armies[army_id], armies, lost, references)
		survivors = {army_id: army for army_id, army in armies.items() if army.soldiers >= 1.0}
		self.world.armies = {army_id: army.to_dict() for army_id, army in sorted(survivors.items())}
		self.bump(ARMIES)
		for owner, killed in sorted(lost.items()):
			self.strike_from_force(owner, killed)
		self._keep_within_force(sorted({army.owner for army in survivors.values()}))
		self._consolidate_conquests()

	def _keep_within_force(self, owners: List[str]) -> None:
		forces = {owner: self.owner_force(owner) for owner in owners}
		self.world.armies = rules.keep_within_force(self.world.armies, owners, forces)
		self.bump(ARMIES)

	def _defend(self, armies: Dict[str, Army]) -> None:
		"""A state no seat plays raises and orders armies to the tiles other owners' armies threaten."""
		played = set(self.needs.played_countries())
		by_tile = {tile: entry["owner"] for tile, entry in self.needs.tile_owner_map().items()}
		records = {army_id: army.to_dict() for army_id, army in armies.items()}
		for owner in sorted(set(by_tile.values()) - played):
			if not self.needs.has_state[owner]:
				continue   # a seat's colony: no state of its own to decide
			for tile, soldiers in army_raising.defence_musters(owner, by_tile, records, self.free_soldiers(owner)):
				made = self.raise_army(owner, soldiers, tile)
				if isinstance(made, Army):
					armies[made.army_id], records[made.army_id] = made, made.to_dict()
			for army_id, tile in army_raising.defence_orders(owner, by_tile, records):
				rules.order(armies[army_id], tile)

	def _campaign_army(self, army: Army, armies: Dict[str, Army], lost: Dict[str, float], references: Dict) -> None:
		owner = army.owner
		reference = references.setdefault(owner, self._reference_equipment(owner))
		modes = self.campaign_modes(owner)
		pay_years = self._pay_years(army)
		days_left = campaign_supply.CAMPAIGN_SEASON_DAYS
		moved = False
		if army.target and army.target != army.tile:
			found = self.needs.route_between(army.tile, army.target, modes)
			if found is None:
				army.log.append({"kind": "no_route", "tile": army.tile, "target": army.target})
				army.target = None
			else:
				camps, army.progress_days, used = campaign_year_rules.march_camps(
					campaign_contest.legs_of(found), army.progress_days, days_left)
				for tile, days in camps:
					army.tile = tile or army.tile
					self._camp(army, days, modes, pay_years, lost)
				days_left -= used
				moved = True
				if army.tile == army.target:
					army.target, army.progress_days = None, 0.0
		occupier = self.needs.tile_owner[army.tile]
		if occupier is not None and occupier != owner and army.soldiers >= 1.0:
			self._contest(army, armies, occupier, days_left, modes, pay_years, lost, reference)
		elif occupier != owner and days_left > 0.0 and army.soldiers >= 1.0:
			self._camp(army, days_left, modes, pay_years, lost)   # in the wild it lives off the land
		elif moved and army.soldiers >= 1.0:
			army.supply_state = 1.0                               # at home, its own state feeds it
