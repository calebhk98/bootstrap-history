"""The household need model as the module's views: the units households want, the basket the actors' budgets read, and the
tonnes a year the home and the partner economies' households buy (rules in household_needs.py)."""
from sim.assembly.api import Part

from . import household_needs, need_substitutes
from .constants import MEAN_INCOME_HOURS_PER_CAPITA


class HouseholdNeeds(Part):

	def __init__(self, module):
		super().__init__(module)
		self._needs_served_by_mods = {}    # installed mod ids -> material -> the needs it serves; data, frozen for the game
		self._climate_baskets = {}         # civilisation id -> (its household basket with the tiles' climate floors, the model); frozen for the game

	def opening_population(self):
		return float(self.needs.civilisation().get("population", self.needs.default_population()))

	def _household_model(self):
		return household_needs.household_model(self.needs.installed_mod_ids(), self.needs.household_need_data)

	def _civilisation_basket(self, base):
		"""The model's basket with the climate floors of the tiles the civilisation holds (kept for the game)."""
		def records():
			tile_ids = self.needs.tiles_listed_by(self.needs.civilisation())
			return household_needs.climate_records(tile_ids, self.needs.tile_climates(tile_ids))
		return household_needs.civilisation_basket(base, str(self.needs.civilisation()["id"]), self._climate_baskets, records)

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

	def household_basket(self):
		"""The household need basket of the civilisation: the installed content's needs with the floors its tiles' climate sets."""
		base, _final = self._household_model()
		return self._civilisation_basket(base)

	def home_household_tonnes(self, prices_in_hours):
		"""{material: tonnes a year} the home households buy at these prices (labour hours a unit), scaled to the opening's people."""
		base, final = self._household_model()
		population = self.opening_population()
		units = household_needs.demand_by_material(base, prices_in_hours, population, MEAN_INCOME_HOURS_PER_CAPITA)
		return household_needs.budget_scaled_final_tonnes(units, prices_in_hours, population, final)

	def _household_need_floors_per_person(self):
		"""What one person's floor of each need costs a year on the seat's tile: the economy's prices and the tile's climate
		floors (the need basket). While the economy opens, the same basket on the goods market."""
		floors = self.parts.market_objects.economy.agent_need_floor_costs_at()
		if floors:
			return dict(floors)
		return self.needs.actor_world().people.need_floor_costs_per_person_year()

	def household_bill_per_person(self):
		"""One person's yearly bill for every need's floor: the figure the founder and an economy household pay."""
		return sum(self._household_need_floors_per_person().values())
