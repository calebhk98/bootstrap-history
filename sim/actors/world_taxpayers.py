"""What a state asks about the people it taxes: who they are, how visible, how far its officials reach."""
from typing import Any, List, Optional, Tuple

from sim.agents.api import demand_answer, taxpayer_income


class Taxpayers:
	"""The home state's taxpayers. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def state_reach(self) -> float:
		return self.needs.state_authority()

	def notice_over(self, scale: float, capacity: Optional[float] = None) -> float:
		return self.needs.notice_over(scale, capacity)

	def levy_shares(self, scale: float, protection: float = 0.0, state: Any = None) -> Any:
		"""(requisition, office) shares of income the state assesses at this visible scale."""
		return self.needs.levy_shares(scale, protection, state)

	def visible_scale_of(self, actor: Any) -> float:
		"""How large and visible any actor looks to the state: its staff, its wealth and its prominence."""
		return self.needs.visible_scale(sum(actor.workforce.values()), demand_answer.visible_wealth(actor.money, actor.stance.concealed_wealth()),
										actor.stance.prominence(), actor.stance.defiance())

	def seat_taxpayers(self, country: Optional[str]) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the playing household seats that belong to `country`; a seat with no
		country belongs to the game's own (home) country."""
		needs = self.needs
		home = self.world.registry.state.home_country
		payers = []
		for seat_id in needs.seat_list()["playing"]:
			if (needs.seat_country[seat_id] or home) == (country or home):
				with needs.act_as(seat_id):
					payers.append((self.acting_seat_visible_scale(), max(0.0, needs.revenue_estimate())))
		return payers

	def acting_seat_visible_scale(self) -> float:
		"""How large and visible the acting seat's household looks to the state: its staff, its wealth and its defiance (a person
		with no prominence of a business's kind)."""
		needs = self.needs
		standing = needs.standing()
		return needs.visible_scale(sum(needs.staff()["employees"].values()),
								   demand_answer.visible_wealth(needs.acting_balance(), float(standing["concealed"])), 0.0, float(standing["defiance"]))

	def firm_taxpayers(self, country: Optional[str]) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the firms with a plant earning in `country`; the income is the part of the firm's
		that its plants on the country's tiles took (a firm with no plant placed elsewhere earns in the country it answers to)."""
		actors = self.world.registry
		home = actors.state.home_country
		return [(self.visible_scale_of(firm), income)
				for firm, income in taxpayer_income.firm_incomes_in(actors.concerns.active_firms(), country or home, actors.countries.country_of,
																	actors.countries.country_of_tile)]

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the home state can see: the home country's playing seats and the firms that answer to it."""
		needs = self.needs
		home = self.world.registry.state.home_country
		payers = self.seat_taxpayers(home)
		if not needs.seat_list()["playing"]:
			with needs.act_as(needs.acting_seat()):
				payers.append((self.acting_seat_visible_scale(), max(0.0, needs.revenue_estimate())))
		return payers + self.firm_taxpayers(home)
