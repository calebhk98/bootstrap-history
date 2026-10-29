"""The household need model as the module's views: the units households want, the basket the actors' budgets read, and the
tonnes a year the home and the partner economies' households buy (rules in household_needs.py)."""
from . import household_needs, need_substitutes
from .constants import MEAN_INCOME_HOURS_PER_CAPITA


class HouseholdNeeds:

	def _household_model(self):
		return household_needs.household_model(self.needs.installed_mod_ids(), self.needs.household_need_data)

	def _needs_served(self):
		"""material -> the needs it serves, for the installed content (built once per set of installed mods)."""
		mods = self.needs.installed_mod_ids()
		served = self._needs_served_by_mods.get(mods)
		if served is None:
			served = self._needs_served_by_mods[mods] = need_substitutes.needs_served(self.needs.household_need_data()["goods"])
		return served

	def materials_serving(self, need_id):
		"""The materials that serve one household need."""
		return need_substitutes.serving(self._needs_served(), need_id)

	def material_substitutes(self, material):
		"""The materials that serve a need `material` serves."""
		return need_substitutes.substitutes_of(self._needs_served(), material)

	def material_serves_a_need(self, material):
		"""Whether the needs data names the material as serving some household need."""
		return need_substitutes.serves_a_need(self._needs_served(), material)

	def household_demand_units(self, prices_in_hours, population, income_per_capita):
		"""{material: units a year} households (and what they buy through recipes) want at these labour-hour prices, with the
		warmth, clothing and shelter floors the civilisation's tiles' climate sets."""
		base, _final = self._household_model()
		basket = household_needs.civilisation_basket(base, self.needs.civilisation(), self.needs.legacy_world_map())
		return household_needs.demand_by_material(base, prices_in_hours, population, income_per_capita, basket)

	def household_basket(self):
		"""The household need basket of the civilisation: the installed content's needs with the floors its tiles' climate sets."""
		base, _final = self._household_model()
		return household_needs.civilisation_basket(base, self.needs.civilisation(), self.needs.legacy_world_map())

	def home_household_tonnes(self, prices_in_hours):
		"""{material: tonnes a year} the home households buy at these prices (labour hours a unit), scaled to the opening's people."""
		base, final = self._household_model()
		population = self.opening_population()
		units = household_needs.demand_by_material(base, prices_in_hours, population, MEAN_INCOME_HOURS_PER_CAPITA)
		return household_needs.budget_scaled_final_tonnes(units, prices_in_hours, population, final)

	def partner_household_demand(self, civilization_id):
		"""{material: tonnes a year} a civilisation's households buy at its own solved prices (remembered for the game)."""
		answer = self._partner_demand.get(civilization_id)
		if answer is None:
			own = self.needs.partner_own_economy[civilization_id]
			per_hour = own["money_per_labour_hour"]
			prices_in_hours = {material: price / per_hour for material, price in own["prices_in_own_coin"].items() if price > 0.0}
			population = float(self.needs.civilisation_record[civilization_id].get("population") or 0.0)
			base, final = self._household_model()
			units = household_needs.demand_by_material(base, prices_in_hours, population, MEAN_INCOME_HOURS_PER_CAPITA)
			answer = self._partner_demand[civilization_id] = household_needs.budget_scaled_final_tonnes(
				units, prices_in_hours, population, final)
		return answer

	def household_need_floors_per_person(self):
		"""What one person's floor of each need costs a year on the seat's tile: the economy's prices and the tile's climate
		floors (the need basket). While the economy opens, the same basket on the goods market."""
		floors = self.economy.agent_need_floor_costs_at()
		if floors:
			return dict(floors)
		return self.needs.actor_world().need_floor_costs_per_person_year()

	def household_bill_per_person(self):
		"""One person's yearly bill for every need's floor: the figure the founder and an economy household pay."""
		return sum(self.household_need_floors_per_person().values())
