"""The agent economy's views: its prices, wages, rents, volumes and the households' cohorts. A read that is None or empty while the
economy opens asks `EconomyPort.answering()` for the parts and reads the part that owns the figure."""
from sim.assembly.api import Part

from . import port_money


class AgentViews(Part):

	def _economy(self):
		return self.parts.market_objects.economy

	def _answering(self):
		return self.parts.market_objects.economy.answering()

	def agent_prices(self):
		"""{good: the agent economy's price now}, or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices()

	def agent_wage(self, trade):
		"""The wage in the acting seat's own labour markets, or None while the agent economy opens."""
		parts = self._answering()
		return None if parts is None else parts.prices.wage_per_hour(trade, self._economy().world.acting_country())

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

	def agent_land_rent(self):
		"""Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
		return self.agent_land_rent_per_hectare()

	def agent_land_rent_per_hectare(self):
		parts = self._answering()
		return None if parts is None else parts.households.land_rent_per_hectare()

	def agent_land_rent_at(self, tile):
		parts = self._answering()
		return None if parts is None else parts.households.land_rent_at_tile(tile)

	def agent_land_rent_paid_by_tile(self):
		parts = self._answering()
		return {} if parts is None else parts.households.land_rent_paid_by_tile()

	def agent_prices_at(self, tile=None):
		"""{good: the agent economy's price in coin} on a tile (the acting one by default), or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices_at(tile)

	def agent_seat_sale_outlook(self, seat_id, material, quantity):
		"""What a seat may count as sold of `quantity` units of a material its concerns make; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.seats.sale_outlook(seat_id, material, quantity)

	def agent_producers_by_good(self):
		"""{good: [(tile, recipe id)]} of the producers the agent economy runs; None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.by_good()

	def agent_producer_runs(self):
		"""[{tile, runs, inputs, outputs}] of each producer that ran last year (runs of its recipe; the recipe's flows per run);
		None while the agent economy opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.runs_last_year()

	def agent_worker_years_by_recipe(self):
		"""Worker-years a year the agent economy's producers put into each recipe; None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.worker_years_by_recipe()

	def agent_trades_good(self, material):
		"""Whether the agent economy has a market for the material (False while it opens)."""
		parts = self._answering()
		return parts is not None and parts.prices.trades_good(material)

	def agent_price_response(self, material, landed_tonnes, taken_tonnes):
		return self.parts.market_objects.economy.agent_price_response(material, landed_tonnes, taken_tonnes)

	def agent_country(self, country):
		"""What the agent economy answers for a partner country in it, or None (not in it, or no wage yet)."""
		parts = self._answering()
		return None if parts is None else parts.households.country(country)

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

	def agent_output_tonnes_by_tile(self):
		"""Tonnes of each good made on each tile last year; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.producers.output_tonnes_by_tile()

	def agent_idle_hours_by_trade(self):
		"""(hours offered and not hired, hours offered) of each trade last year; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.households.idle_hours_by_trade()

	def agent_fugitive_share_by_tile(self):
		"""{tile: share of its people away having fled the state's take}; empty before the agent economy exists."""
		return self.parts.market_objects.economy.parts.households.fugitive_share_by_tile()

	def agent_opening_basket(self):
		"""(units a year households bought at the opening, their opening prices in labour hours), or None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.households.opening_basket(None)

	def agent_volume_baseline(self):
		"""{good: the volume traded in the first year it cleared any}, or None before a year has closed."""
		parts = self._answering()
		return None if parts is None else parts.households.volume_baseline(None)

	def agent_traded_volumes(self):
		"""{good: units the home markets traded last year}, or None before a year has closed."""
		parts = self._answering()
		return None if parts is None else parts.households.traded_volumes(None)

	def agent_producer_capacity(self, material):
		"""Tonnes a year the agent economy's producers can make of a material; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.producers.capacity_tonnes(material)

	def producers_stamp(self):
		"""Changes whenever the economy's producers do (as its year closes)."""
		return int(self._economy().world.agent_record().get("years_run", 0))

	def producer_capacities(self):
		"""[(recipe id, capacity in runs)] of every producer in the opened agent economy; empty before it opens."""
		return self._economy().parts.producers.capacities()

	def goods_carried_last_year(self):
		"""Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}."""
		return self.parts.market_objects.economy.agent.carried_last_year()

	def country_trade_book(self, country):
		"""{good: tonnes and value each way} of what crossed the country's border last year; empty while the economy opens."""
		parts = self._answering()
		return {} if parts is None else parts.households.trade_book(country)

	def country_opening_basket(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.opening_basket(country)

	def country_volume_baseline(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.volume_baseline(country)

	def country_traded_volumes(self, country):
		parts = self._answering()
		return None if parts is None else parts.households.traded_volumes(country)

	def fleet_goods(self, holder_id):
		return self.parts.market_objects.economy.fleet_goods(holder_id)

	def economy_output_value(self):
		return port_money.output_value(self._economy().world)

	def coin_stock_value(self):
		return port_money.coin_stock_value(self._economy().world)

	def agent_rate(self):
		"""The agent economy's loanable-funds rate, or None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.prices.rate()

	def agent_credit_room(self, borrower_id):
		"""(True, room) when the agent economy answers, with room None before lenders have met; (False, None) while it opens."""
		parts = self._answering()
		return (False, None) if parts is None else (True, parts.prices.credit_room(borrower_id))

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
		return self._economy().agent.spin_up_result()

	def agent_health(self, metals=(), staple=None):
		"""The agent economy's health figures over the years this game has played (port_health.py)."""
		from .port_health import health_report
		return health_report(self._economy().agent, metals, staple)

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
