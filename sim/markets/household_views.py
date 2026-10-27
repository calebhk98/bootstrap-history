"""The household need model as the module's views: the units households want, the basket the actors' budgets read, and the
tonnes a year the home and the partner economies' households buy (rules in household_needs.py)."""
from . import household_needs
from .constants import MEAN_INCOME_HOURS_PER_CAPITA


class HouseholdNeeds:

	def _household_model(self):
		return household_needs.household_model(self.needs.installed_mod_ids(), self.needs.household_need_data)

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
