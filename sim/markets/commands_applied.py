"""The commands the markets module applies."""
from sim.assembly.api import RepriceTree
from sim.economy import api as economy_api
from sim.ledger.api import RescaleHouseholdMoney
from sim.rekey import rekey


class Applying:

	def reset_draws(self, command):
		self.goods_market.reset_draws()

	def note_draw(self, command):
		self.goods_market.note_draw(command.commodity, command.tonnes)

	def note_purchase(self, command):
		market = self.goods_market
		market.note_purchase(market.acting_party_id, command.commodity, command.tonnes)

	def forget_actor_orders(self, command):
		self.economy.forget_actor_orders(command.actor_id)

	def note_actor_sale(self, command):
		self.economy.note_actor_sale(command.seller_id, command.material, command.tonnes, command.from_concerns)

	def note_actor_purchase(self, command):
		self.economy.note_actor_purchase(command.buyer_id, command.commodity, command.tonnes, command.budget)

	def open_market_book_command(self, command):
		self.open_market_book()

	def rename_market_seat(self, command):
		self.economy.agent.rename_agent(command.from_id, command.to_id)
		if self.world.market_flows:
			rekey(self.world.market_flows, command.from_id, command.to_id)
		self.goods_market.forget_seat_party(command.from_id)

	def mark_money_priced_at_economy(self, command):
		self.world.money_from_economy = True

	def reprice_opening_money(self, command):
		"""From now the money an hour of work is worth is the economy's unskilled wage. `command.before` is the figure the
		game's money was counted at; every seat's purse and the tree's money fields move by the ratio of the two."""
		self.mark_money_priced_at_economy(command)
		ratio = self.needs.money_per_labour_hour() / command.before
		for seat_id in self.needs.registered_seats():
			with self.act_as(seat_id):
				self.needs.send(RescaleHouseholdMoney(ratio))
		self.needs.send(RepriceTree())

	def buy_material(self, command):
		market = self.goods_market
		return market.buy(market.acting, command.material, command.tonnes)

	def sell_material(self, command):
		market = self.goods_market
		return market.sell(market.acting, command.material, command.tonnes)

	def found_bank_from_outside(self, command):
		agent = self.economy.agent
		if not agent.opened():
			return None
		economy = agent.economy()
		units = float(command.capital) / economy.setup.coin_per_unit
		bank = economy_api.found_bank_from_outside(economy, self.clock.acting_seat, units, self.needs.year(), economy_api.EDGE_EXCHANGE)
		return None if bank is None else bank.agent_id
