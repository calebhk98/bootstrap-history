"""The commands the markets module applies."""


class Applying:

	def reset_draws(self, command):
		self._market().reset_draws()

	def note_draw(self, command):
		self._market().note_draw(command.commodity, command.tonnes)

	def note_purchase(self, command):
		market = self._market()
		market.note_purchase(market.acting_party_id, command.commodity, command.tonnes)

	def forget_actor_orders(self, command):
		self._economy().forget_actor_orders(command.actor_id)

	def note_actor_sale(self, command):
		self._economy().note_actor_sale(command.seller_id, command.material, command.tonnes, command.from_concerns)

	def note_actor_purchase(self, command):
		self._economy().note_actor_purchase(command.buyer_id, command.commodity, command.tonnes, command.budget)
