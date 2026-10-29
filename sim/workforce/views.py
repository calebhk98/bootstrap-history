"""The views the workforce module publishes."""
from sim.demography.api import DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR
from sim.labour.api import wage_provider
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

from . import rules
from .constants import BASE_WORKING_DAY_HOURS, WAGE_SCARCITY_ELASTICITY


class Views:

	# ---- people ----

	def staff_snapshot(self):
		"""Headcount by trade now, to diff against after something trims it."""
		return self.labour.staff_snapshot()

	def headcount(self):
		return self.labour.headcount()

	def hours_available(self, pool):
		labour = self.labour
		return {"scholar_hands": labour.scholar_hands_available, "craft_hands": labour.craft_hands_available,
		        "director_pool": labour.director_pool, "director_committed": labour.director_hours_committed,
		        "hired_cap": labour.hired_cap}[pool]()

	def hours_you_can_call_on(self, trade):
		"""The hours a year of a trade the seat can call on: the market's supply plus the time it has already bought."""
		return self.labour.hours_you_can_call_on(trade)

	def effective_scholars(self):
		"""The scholars the seat counts (the founder included, while alive)."""
		return self.labour.effective_scholars()

	def literacy_references(self):
		"""The literacy figures hiring and research are measured against."""
		labour = self.labour
		return {"factor_cap": labour.LITERACY_FACTOR_CAP, "reference_elite": labour.LITERACY_REFERENCE_ELITE,
		        "reference_general": labour.LITERACY_REFERENCE_GENERAL}

	def literacy_capacity(self, trade):
		"""The most people of `trade` the country's literacy lets the seat hire or teach."""
		return self.labour.literate_capacity(trade)

	def farm_share_of_hours(self):
		return self.labour.farm_share_of_hours()

	def training_advice(self, trade_id):
		"""The facts of teaching one person `trade_id`, read from the labour market. `hours_each` and `years` are None when
		no trade here can teach it."""
		labour = self.labour
		source = labour._source_trade_for(trade_id)
		return {"trade": trade_id,
		        "source_trade": source,
		        "hours_each": labour.training_hours_per_person(trade_id, source) if source else None,
		        "years": labour.training_years_from(trade_id, source) if source else None}

	def staff_advice(self, kind, deficit=None):
		return self.labour.staff_advice(kind, deficit)

	def project_staffing_shortfall(self, node):
		return self.labour.project_staffing_shortfall(node)

	def seat_base_tile(self, seat_id):
		"""Where the seat works from (its household's base tile, else the capital's)."""
		with self.needs.act_as(seat_id):
			return self.labour.base_tile()

	def available_trades(self):
		return self.labour.available_trades()

	def is_craft_trade(self, trade):
		return self.labour.is_craft_trade(trade)

	def taught_trade_people(self, trade):
		return self.labour.taught_trade_people(trade)

	def people_who_exist(self, trade):
		return self.labour.people_who_exist(trade)

	def reachable_trade_population(self, trade):
		return self.labour.reachable_trade_population(trade)

	def local_market_share(self):
		return self.labour.local_market_share()

	def base_tile(self):
		"""Where the acting seat works from."""
		return self.labour.base_tile()

	def labour_market(self):
		"""The one labour market every employer asks: quote, hire, release, read the pressure (the object itself)."""
		return self.labour.market

	# ---- the market and the wage ----

	def market_supply(self, trade):
		return self.labour.market_supply(trade)

	def trade_available(self, trade):
		return self.labour.trade_available(trade)

	def labour_quote(self, trade, hours):
		"""Money one hour of a trade costs when `hours` of it are bought at once (the price rises with the hours)."""
		return self.labour.labour_market.quote(trade, hours)

	def hour_wage(self, trade):
		"""Money one hour of a trade costs now."""
		return self.labour.market.quote(trade)

	def wage(self, trade):
		"""Money one hour of a trade is worth on the wage schedule (the labour market's quote is `hour_wage`)."""
		return self.labour.wage_per_hour(trade)

	def base_annual_wage(self, trade):
		"""A year's wage of a trade on the opening schedule."""
		return self.labour.base_annual_wage(trade)

	def trade_population(self, trade):
		"""An estimate of the people who ply a trade across the country."""
		return self.labour.national_trade_population(trade)

	def money_per_labour_hour(self):
		return self.labour.money_per_labour_hour()

	def opening_money_per_labour_hour(self):
		return self.labour.opening_wage_schedule().opening_money_per_labour_hour

	def labour_state_weights(self):
		"""The weight the labour market's own trait table gives each trait the state cares about."""
		return self.labour.STATE_WEIGHTS

	def town_mortality_premium_by_tile(self):
		"""{tile: premium} for the tiles whose town carries a mortality premium from a registered provider (a share of the
		baseline death rate); empty with no provider."""
		return self.labour.town_mortality_premium_by_tile()

	def wage_index_terms(self):
		"""What the wage index is measured against: the base year's index and how much scarcer labour raises its own price."""
		return {"base": self.needs.opening_wage_index(), "elasticity": WAGE_SCARCITY_ELASTICITY}

	def wage_index(self):
		"""Labour is dearer the further the nation's people sit below what its unshocked trend would hold."""
		terms = self.wage_index_terms()
		unshocked_trend = max(POP_SCALE_FLOOR, float(self.needs.civilisation().get("population", DEFAULT_POPULATION_100AD))
		                      / DEFAULT_POPULATION_100AD)
		return rules.wage_index_of(terms["base"], terms["elasticity"], self.needs.pop_scale(), unshocked_trend)

	def wage_materials(self):
		"""The materials a wage is set against, in order: the staple (Complaint 762: the trades' tool materials were meant to
		follow and never do)."""
		return [wage_provider.staple_material(self.needs.civilisation())]

	def trade_registry(self):
		"""{trade id: {family, training_years, ...the trade's extra fields}}."""
		return self.labour._world.trade_registry

	# ---- the farm ----

	def farming_technique(self):
		"""The society's farming technique (rotation, toolkit, crop) from what it knows."""
		return self.labour.farming_technique()

	def farm_land_hectares(self):
		"""The hectares the society's farm workforce works (the area the farmland model is sized for)."""
		return self.needs.farm_land().hectares

	# ---- the working day ----

	def extra_lit_hours_per_day(self):
		"""Hours a day added by the open works that declare `working_day`, each for the people it covers."""
		works = []
		working_day = self.needs.mechanic["working_day"]
		covering = self.needs.coverage()
		for node_id in tuple(working_day):
			if not self.needs.running[node_id]:
				continue
			share = self.needs.coverage_share[node_id] if node_id in covering else 1.0
			works.append((working_day[node_id]["extra_hours_per_day"], share))
		return rules.extra_lit_hours(works)

	def hours_per_person_year(self):
		"""Hours one person gives in a year: the convention, stretched by the lit hours added to the day."""
		if not self.needs.mechanic["working_day"]:
			return HOURS_PER_PERSON_YEAR
		return rules.working_hours_per_year(HOURS_PER_PERSON_YEAR, self.extra_lit_hours_per_day(), BASE_WORKING_DAY_HOURS)
