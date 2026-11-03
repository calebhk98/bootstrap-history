"""The agent economy's labour views: wages, the people by trade and tile, idle hours and the household cohorts' incomes."""
from sim.economy import api as economy_api

from .agent_view_part import AgentViewPart


class AgentLabourViews(AgentViewPart):

	def agent_wage(self, trade):
		"""The wage in the acting seat's own labour markets, or None while the agent economy opens."""
		parts = self._answering()
		return None if parts is None else parts.prices.wage_per_hour(trade, self._economy().world.scenario.acting_country())

	def agent_unskilled_wage(self):
		"""Money one hour of the unskilled trade is paid in the agent economy; None until the game's money is priced at it."""
		if not self._economy().world.money_from_economy():
			return None
		parts = self._answering()
		return None if parts is None else parts.prices.unskilled_wage_per_hour()

	def agent_people_by_trade(self):
		economy = self._economy()
		return None if economy.opening else economy.parts.producers.people_by_trade()

	def agent_people_by_tile_and_trade(self):
		economy = self._economy()
		return None if economy.opening else economy.parts.producers.people_by_tile_and_trade()

	def agent_worker_years_by_recipe(self):
		"""Worker-years a year the agent economy's producers put into each recipe; None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.worker_years_by_recipe()

	def agent_idle_hours_by_trade(self):
		"""(hours offered and not hired, hours offered) of each trade last year; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.households.idle_hours_by_trade()

	def agent_trades(self):
		"""The trades the running agent economy's labour core has markets for."""
		return economy_api.economy_trades(self.parts.market_objects.economy.agent.economy())

	def agent_cohort_incomes(self):
		"""[(people, yearly money income)] of the household cohorts, poorest per head first; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.households.cohort_incomes()

	def agent_cohort_land_rents(self, tiles):
		"""[(people, rent received in coin)] in the order of `agent_cohort_incomes`; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.households.cohort_land_rents(tiles)

	def agent_need_floor_costs(self):
		"""What a person's floor of each need costs a year on the home tiles, in coin; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.households.need_floor_costs_per_person_year() or None
