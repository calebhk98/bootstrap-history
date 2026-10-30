"""The agent economy's views: its prices, wages, rents, volumes and the households' cohorts."""


class AgentViews:

	def agent_prices(self):
		"""{good: the agent economy's price now}, or None while the economy opens."""
		return self.economy.agent_prices()

	def agent_wage(self, trade):
		"""The wage in the acting seat's own labour markets, or None while the agent economy opens."""
		return self.economy.agent_wage_per_hour(trade)

	def agent_unskilled_wage(self):
		"""Money one hour of the unskilled trade is paid in the agent economy; None until the game's money is priced at it."""
		return self.economy.unskilled_wage()

	def agent_people_by_trade(self):
		return self.economy.agent_people_by_trade()

	def agent_people_by_tile_and_trade(self):
		return self.economy.agent_people_by_tile_and_trade()

	def agent_land_rent(self):
		"""Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
		return self.economy.agent_land_rent_per_hectare()

	def agent_land_rent_per_hectare(self):
		return self.economy.agent_land_rent_per_hectare()

	def agent_land_rent_at(self, tile):
		return self.economy.agent_land_rent_at(tile)

	def agent_land_rent_paid_by_tile(self):
		return self.economy.agent_land_rent_paid_by_tile()

	def agent_prices_at(self, tile=None):
		"""{good: the agent economy's price in coin} on a tile (the acting one by default), or None while the economy opens."""
		return self.economy.agent_prices_at(tile)

	def agent_seat_sale_outlook(self, seat_id, material, quantity):
		"""What a seat may count as sold of `quantity` units of a material its concerns make; None while the economy opens."""
		return self.economy.agent_seat_sale_outlook(seat_id, material, quantity)

	def agent_producers_by_good(self):
		"""{good: [(tile, recipe id)]} of the producers the agent economy runs; None while it opens."""
		return self.economy.agent_producers_by_good()

	def agent_producer_runs(self):
		"""[{tile, runs, inputs, outputs}] of each producer that ran last year (runs of its recipe; the recipe's flows per run);
		None while the agent economy opens."""
		return self.economy.agent_producer_runs()

	def agent_worker_years_by_recipe(self):
		"""Worker-years a year the agent economy's producers put into each recipe; None while it opens."""
		return self.economy.agent_worker_years_by_recipe()

	def agent_trades_good(self, material):
		return self.economy.agent_trades_good(material)

	def agent_price_response(self, material, landed_tonnes, taken_tonnes):
		return self.economy.agent_price_response(material, landed_tonnes, taken_tonnes)

	def agent_country(self, country):
		return self.economy.agent_country(country)

	def agent_cohort_incomes(self):
		return self.economy.agent_cohort_incomes()

	def agent_cohort_land_rents(self, tiles):
		return self.economy.agent_cohort_land_rents(tiles)

	def agent_need_floor_costs(self):
		return self.economy.agent_need_floor_costs()

	def agent_output_tonnes_by_tile(self):
		return self.economy.agent_output_tonnes_by_tile()

	def agent_idle_hours_by_trade(self):
		return self.economy.agent_idle_hours_by_trade()

	def agent_fugitive_share_by_tile(self):
		"""{tile: share of its people away having fled the state's take}; empty before the agent economy exists."""
		agent = self.economy.agent
		return {} if agent is None else agent.fugitive_share_by_tile()

	def agent_opening_basket(self):
		"""(units a year households bought at the opening, their opening prices in labour hours), or None while it opens."""
		return self.economy.agent_opening_basket()

	def agent_volume_baseline(self):
		"""{good: the volume traded in the first year it cleared any}, or None before a year has closed."""
		return self.economy.agent_volume_baseline()

	def agent_traded_volumes(self):
		"""{good: units the home markets traded last year}, or None before a year has closed."""
		return self.economy.agent_traded_volumes()

	def agent_producer_capacity(self, material):
		"""Tonnes a year the agent economy's producers can make of a material; None while the economy opens."""
		return self.economy.agent_producer_capacity_tonnes(material)

	def producers_stamp(self):
		"""Changes whenever the economy's producers do (as its year closes)."""
		return self.economy.producers_stamp()

	def producer_capacities(self):
		return self.economy.producer_capacities()

	def goods_carried_last_year(self):
		"""Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}."""
		return self.economy.agent.carried_last_year()

	def country_opening_basket(self, country):
		return self.economy.agent_opening_basket(country)

	def country_volume_baseline(self, country):
		return self.economy.agent_volume_baseline(country)

	def country_traded_volumes(self, country):
		return self.economy.agent_traded_volumes(country)

	def fleet_goods(self, holder_id):
		return self.economy.fleet_goods(holder_id)

	def economy_output_value(self):
		return self.economy.output_value()

	def coin_stock_value(self):
		return self.economy.coin_stock_value()

	def agent_rate(self):
		"""The agent economy's loanable-funds rate, or None while it opens."""
		return self.economy.agent_rate()

	def agent_credit_room(self, borrower_id):
		"""(True, room) when the agent economy answers, with room None before lenders have met; (False, None) while it opens."""
		return self.economy.agent_credit_room(borrower_id)

	def agent_economy_opened(self):
		return self.economy.agent.opened()
