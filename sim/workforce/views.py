"""The views the workforce module publishes."""
from sim.assembly.api import Part
from sim.labour.api import STATE_WEIGHTS, wage_provider
from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world.farm_labour import hours_per_working_day

from . import rules


class Views(Part):

	# ---- people ----

	def headcount(self):
		return self.parts.core.labour.book.headcount()

	def hours_available(self, pool):
		labour = self.parts.core.labour
		return {"scholar_hands": labour.hands.scholar_hands_available, "craft_hands": labour.hands.craft_hands_available,
		        "director_pool": labour.hours.director_pool, "director_committed": labour.hours.director_hours_committed,
		        "hired_cap": labour.supply.market_hours_offered}[pool]()

	def hours_you_can_call_on(self, trade):
		"""The hours a year of a trade the seat can call on: the market's supply plus the time it has already bought."""
		return self.parts.core.labour.hands.hours_you_can_call_on(trade)

	def effective_scholars(self):
		"""The scholars the seat counts (the founder included, while alive)."""
		return self.parts.core.labour.hands.effective_scholars()

	def literacy_references(self):
		"""The literacy figures hiring and research are measured against."""
		labour = self.parts.core.labour
		return {"factor_cap": labour.trades.LITERACY_FACTOR_CAP, "reference_elite": labour.trades.LITERACY_REFERENCE_ELITE,
		        "reference_general": labour.trades.LITERACY_REFERENCE_GENERAL}

	def literacy_capacity(self, trade):
		"""The most people of `trade` the country's literacy lets the seat hire or teach."""
		return self.parts.core.labour.supply.literate_capacity(trade)

	def farm_share_of_hours(self):
		return self.parts.core.labour.allocation.farm_share_of_hours()

	def training_advice(self, trade_id):
		"""The facts of teaching one person `trade_id`, read from the labour market. `hours_each` and `years` are None when
		no trade here can teach it."""
		labour = self.parts.core.labour
		source = labour.training.source_trade_for(trade_id)
		return {"trade": trade_id,
		        "source_trade": source,
		        "hours_each": labour.training.training_hours_per_person(trade_id, source) if source else None,
		        "years": labour.training.training_years_from(trade_id, source) if source else None}

	def staff_advice(self, kind, deficit=None):
		return self.parts.core.labour.advice.staff_advice(kind, deficit)

	def project_staffing_shortfall(self, node):
		return self.parts.core.labour.supply.project_staffing_shortfall(node)

	def seat_base_tile(self, seat_id):
		"""Where the seat works from (its household's base tile, else the capital's)."""
		with self.needs.act_as(seat_id):
			return self.parts.core.labour.settlement.base_tile()

	def available_trades(self):
		return self.parts.core.labour.trades.available_trades()

	def is_craft_trade(self, trade):
		return self.parts.core.labour.trades.is_craft_trade(trade)

	def taught_trade_people(self, trade):
		return self.parts.core.labour.supply.taught_trade_people(trade)

	def people_who_exist(self, trade):
		return self.parts.core.labour.supply.people_who_exist(trade)

	def reachable_trade_population(self, trade):
		return self.parts.core.labour.supply.reachable_trade_population(trade)

	def labour_reach_block(self, trades):
		"""(reachable_trade_population, people_who_exist) of each trade given, as two arrays."""
		return self.parts.core.labour.supply.reach_block(trades)

	def base_tile(self):
		"""Where the acting seat works from."""
		return self.parts.core.labour.settlement.base_tile()

	def labour_market(self):
		"""The one labour market every employer asks: quote the economy's wage (the object itself)."""
		return self.parts.core.labour.market

	# ---- the market and the wage ----

	def market_supply(self, trade):
		return self.parts.core.labour.supply.market_supply(trade)

	def trade_available(self, trade):
		return self.parts.core.labour.trades.trade_available(trade)

	def labour_quote(self, trade):
		"""Money one hour of a trade costs now: the one wage of the trade."""
		return self.parts.core.labour.market.quote(trade)

	def wage(self, trade):
		"""Money one hour of a trade is worth on the wage schedule (the labour market's quote is `labour_quote`)."""
		return self.parts.core.labour.schedule.wage_per_hour(trade)

	def base_annual_wage(self, trade):
		"""A year's wage of a trade on the opening schedule."""
		return self.parts.core.labour.schedule.base_annual_wage(trade)

	def trade_population(self, trade):
		"""An estimate of the people who ply a trade across the country."""
		return self.parts.core.labour.supply.national_trade_population(trade)

	def money_per_labour_hour(self):
		return self.parts.core.labour.schedule.money_per_labour_hour()

	def opening_money_per_labour_hour(self):
		return self.parts.core.labour.schedule.opening_wage_schedule().money_per_labour_hour

	def labour_state_weights(self):
		"""The weight the labour market's own trait table gives each trait the state cares about."""
		return STATE_WEIGHTS

	def town_mortality_premium_by_tile(self):
		"""{tile: premium} for the tiles whose town carries a mortality premium from a registered provider (a share of the
		baseline death rate); empty with no provider."""
		return self.parts.core.labour.settlement.town_mortality_premium_by_tile()

	def cleared_wage_change(self):
		"""How far the unskilled hour's cleared wage moved between the last two clearings, as a share; None before there are two."""
		society = self.world
		if not society.cleared_wage or not society.cleared_wage_before:
			return None
		return society.cleared_wage / society.cleared_wage_before - 1.0

	def wage_materials(self):
		"""The materials a wage is set against, in order: the staple, then every trade's tool materials."""
		return rules.wage_materials_of(wage_provider.staple_material(self.needs.civilisation()), self.trade_registry())

	def trade_registry(self):
		"""{trade id: {family, training_years, ...the trade's extra fields}}."""
		return self.parts.core.reads.trades.trade_registry

	# ---- the farm ----

	def farming_technique(self):
		"""The society's farming technique (rotation, toolkit, crop) from what it knows."""
		return self.parts.core.labour.allocation.farming_technique()

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
		return rules.working_hours_per_year(HOURS_PER_PERSON_YEAR, self.extra_lit_hours_per_day(), hours_per_working_day())
