from sim.assembly.api import Part
"""The agent economy's views: its prices, wages, rents, volumes and the households' cohorts."""


class AgentViews(Part):

	def agent_prices(self):
		"""{good: the agent economy's price now}, or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices()

	def agent_wage(self, trade):
		"""The wage in the acting seat's own labour markets, or None while the agent economy opens."""
		return self.parts.market_objects.economy.agent_wage_per_hour(trade)

	def agent_unskilled_wage(self):
		"""Money one hour of the unskilled trade is paid in the agent economy; None until the game's money is priced at it."""
		return self.parts.market_objects.economy.unskilled_wage()

	def agent_people_by_trade(self):
		return self.parts.market_objects.economy.agent_people_by_trade()

	def agent_people_by_tile_and_trade(self):
		return self.parts.market_objects.economy.agent_people_by_tile_and_trade()

	def agent_land_rent(self):
		"""Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
		return self.parts.market_objects.economy.agent_land_rent_per_hectare()

	def agent_land_rent_per_hectare(self):
		return self.parts.market_objects.economy.agent_land_rent_per_hectare()

	def agent_land_rent_at(self, tile):
		return self.parts.market_objects.economy.agent_land_rent_at(tile)

	def agent_land_rent_paid_by_tile(self):
		return self.parts.market_objects.economy.agent_land_rent_paid_by_tile()

	def agent_prices_at(self, tile=None):
		"""{good: the agent economy's price in coin} on a tile (the acting one by default), or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices_at(tile)

	def agent_seat_sale_outlook(self, seat_id, material, quantity):
		"""What a seat may count as sold of `quantity` units of a material its concerns make; None while the economy opens."""
		return self.parts.market_objects.economy.agent_seat_sale_outlook(seat_id, material, quantity)

	def agent_producers_by_good(self):
		"""{good: [(tile, recipe id)]} of the producers the agent economy runs; None while it opens."""
		return self.parts.market_objects.economy.agent_producers_by_good()

	def agent_producer_runs(self):
		"""[{tile, runs, inputs, outputs}] of each producer that ran last year (runs of its recipe; the recipe's flows per run);
		None while the agent economy opens."""
		return self.parts.market_objects.economy.agent_producer_runs()

	def agent_worker_years_by_recipe(self):
		"""Worker-years a year the agent economy's producers put into each recipe; None while it opens."""
		return self.parts.market_objects.economy.agent_worker_years_by_recipe()

	def agent_trades_good(self, material):
		return self.parts.market_objects.economy.agent_trades_good(material)

	def agent_price_response(self, material, landed_tonnes, taken_tonnes):
		return self.parts.market_objects.economy.agent_price_response(material, landed_tonnes, taken_tonnes)

	def agent_country(self, country):
		return self.parts.market_objects.economy.agent_country(country)

	def agent_cohort_incomes(self):
		return self.parts.market_objects.economy.agent_cohort_incomes()

	def agent_cohort_land_rents(self, tiles):
		return self.parts.market_objects.economy.agent_cohort_land_rents(tiles)

	def agent_need_floor_costs(self):
		return self.parts.market_objects.economy.agent_need_floor_costs()

	def agent_output_tonnes_by_tile(self):
		return self.parts.market_objects.economy.agent_output_tonnes_by_tile()

	def agent_idle_hours_by_trade(self):
		return self.parts.market_objects.economy.agent_idle_hours_by_trade()

	def agent_fugitive_share_by_tile(self):
		"""{tile: share of its people away having fled the state's take}; empty before the agent economy exists."""
		return self.parts.market_objects.economy.parts.households.fugitive_share_by_tile()

	def agent_opening_basket(self):
		"""(units a year households bought at the opening, their opening prices in labour hours), or None while it opens."""
		return self.parts.market_objects.economy.agent_opening_basket()

	def agent_volume_baseline(self):
		"""{good: the volume traded in the first year it cleared any}, or None before a year has closed."""
		return self.parts.market_objects.economy.agent_volume_baseline()

	def agent_traded_volumes(self):
		"""{good: units the home markets traded last year}, or None before a year has closed."""
		return self.parts.market_objects.economy.agent_traded_volumes()

	def agent_producer_capacity(self, material):
		"""Tonnes a year the agent economy's producers can make of a material; None while the economy opens."""
		return self.parts.market_objects.economy.agent_producer_capacity_tonnes(material)

	def producers_stamp(self):
		"""Changes whenever the economy's producers do (as its year closes)."""
		return self.parts.market_objects.economy.producers_stamp()

	def producer_capacities(self):
		return self.parts.market_objects.economy.producer_capacities()

	def goods_carried_last_year(self):
		"""Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}."""
		return self.parts.market_objects.economy.agent.carried_last_year()

	def country_trade_book(self, country):
		"""{good: tonnes and value each way} of what crossed the country's border last year; empty while the economy opens."""
		return self.parts.market_objects.economy.agent_trade_book(country)

	def country_opening_basket(self, country):
		return self.parts.market_objects.economy.agent_opening_basket(country)

	def country_volume_baseline(self, country):
		return self.parts.market_objects.economy.agent_volume_baseline(country)

	def country_traded_volumes(self, country):
		return self.parts.market_objects.economy.agent_traded_volumes(country)

	def fleet_goods(self, holder_id):
		return self.parts.market_objects.economy.fleet_goods(holder_id)

	def economy_output_value(self):
		return self.parts.market_objects.economy.output_value()

	def coin_stock_value(self):
		return self.parts.market_objects.economy.coin_stock_value()

	def agent_rate(self):
		"""The agent economy's loanable-funds rate, or None while it opens."""
		return self.parts.market_objects.economy.agent_rate()

	def agent_credit_room(self, borrower_id):
		"""(True, room) when the agent economy answers, with room None before lenders have met; (False, None) while it opens."""
		return self.parts.market_objects.economy.agent_credit_room(borrower_id)

	def agent_economy_opened(self):
		return self.parts.market_objects.economy.agent.opened()

	# ---- the economy's own life: its opening, its record, its last year, for the engine's year and the tools ----

	def open_agent_economy(self):
		"""Open the agent economy (with its hidden spin-up) if it is not open, and count the game's money at its wage."""
		self.parts.market_objects.economy.open_agent()

	def flush_agent_record(self):
		"""Bring the saved copy of the agent economy up to date; the game's save asks first."""
		self.parts.market_objects.economy.flush_record()

	def agent_spin_up_result(self):
		"""How the opening's hidden first stage ended: {"settled", "years", "gap"}; empty while it opens or when none ran."""
		return self.parts.market_objects.economy.spin_up_result()

	def agent_health(self, metals=(), staple=None):
		"""The agent economy's health figures over the years this game has played (port_health.py)."""
		return self.parts.market_objects.economy.health(metals, staple)

	def agent_last_outcome(self):
		"""The agent economy's outcome for the last year this process ran (its accounts, wages and prices); None on a game
		loaded and not yet stepped, since the outcome is not saved (the health figures are: agent_health)."""
		return self.parts.market_objects.economy.parts.year.last_outcome

	def agent_economy_setup(self):
		"""The setup the running agent economy was opened with."""
		return self.parts.market_objects.economy.agent.economy().setup

	def agent_stale_goods(self):
		"""The goods whose markets did not clear lately: their shown price is what they would cost to make, not a trade."""
		return self.parts.market_objects.economy.parts.prices.stale_goods()

	def agent_traded_staple(self):
		"""The staple good households buy most of whose market cleared lately; None when none did."""
		from .port_trace import traded_staple
		return traded_staple(self.parts.market_objects.economy.agent, self.agent_stale_goods())

	def agent_opening_setup(self):
		"""The setup of the opening this game saved."""
		from .port_setup import build_setup
		world = self.parts.market_objects.economy.world
		return build_setup(world, world.agent_record()["opening"])
