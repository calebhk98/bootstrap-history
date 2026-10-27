"""The commands the markets module applies."""
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

	def buy_material(self, command):
		market = self.goods_market
		return market.buy(market.acting, command.material, command.tonnes)

	def sell_material(self, command):
		market = self.goods_market
		return market.sell(market.acting, command.material, command.tonnes)
