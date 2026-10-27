"""The founder's household answers the state's demands: the requisition and the supply levy it assesses, and a confiscation.

This reads the household's stance, the state's reach and its protection and rolls the enforcement. A household that complies
draws no random number, so complying leaves the game's stream as it was.

Needs: legacy_dice, state_treasury, legacy_game, acting_balance, legacy_acting_household, transfer_listening, send (PayEdge,
RecordEvent)."""
from sim.agents.api import demand_answer, edges
from sim.hazards.api import capital_lost
from sim.ledger.api import PayEdge, TakeFromHouseholdPurse
from sim.reporting.api import RecordEvent

from . import state_demand
from .state_demand import PAYS_IN_FULL


class Demands:

	def answer_state_demand(self, amount):
		"""What the household pays on a demand of `amount` given how it has chosen to answer. A refusal marks the household in
		the state's eyes and puts blame on it; a service offered in negotiation is paid to the people who render it."""
		seat = self.seat
		stance = seat.demand_stance
		draw = self.needs.legacy_dice().random() if stance not in PAYS_IN_FULL else 1.0
		answer = demand_answer.settle_demand(stance, amount, self.state_reach(), seat.protection, draw, seat.service_offer)
		if answer["service"] > 0.0:
			self.needs.send(PayEdge(edges.EDGE_STATE_SPENDING, answer["service"], "service to the state"))
		if answer["refused"]:
			seat.defiance = demand_answer.defiance_after_refusal(seat.defiance)
			seat.scandal += demand_answer.blame_for_refusal(True)
		return answer

	def lose_capital_to(self, fraction, cause, taker_id):
		"""A fraction of what the household holds goes to the actor `taker_id` (the state's treasury is not a named edge); the sum taken."""
		lost = capital_lost(self.needs.legacy_acting_household().capital, fraction)
		if lost <= 0.0:
			return 0.0
		self.needs.send(TakeFromHouseholdPurse(taker_id, lost, cause))
		return lost

	def answer_confiscation(self, fraction, cause):
		"""The state demands `fraction` of the wealth it can see (the purse less what the household has hidden, plus registered
		claims on other actors). The household answers like any demand; what is paid is taken to the treasury, from the purse
		first and then from the claims. Returns (the answer, what was demanded, what was taken)."""
		game = self.needs.legacy_game()
		capital = self.needs.acting_balance()
		registered = self.needs.wealth_claims()
		claims = sum(max(0.0, reader(game)) for reader, _seizer in registered)
		demanded = demand_answer.visible_wealth(capital + claims, self.seat.concealed) * max(0.0, min(1.0, fraction))
		answer = self.answer_state_demand(demanded)
		taken = 0.0
		paid = answer["paid"]
		if paid > 0.0 and capital > 0.0:
			purse_part = min(paid, capital)
			taken = self.lose_capital_to(purse_part / capital, cause, self.needs.state_treasury().actor_id)
			paid -= purse_part
		if paid > 0.0:
			for _reader, seizer in registered:
				seized = max(0.0, seizer(game, paid, self.needs.state_treasury()))
				taken += seized
				paid -= seized
				if paid <= 0.0:
					break
		return answer, demanded, taken

	def settle_household_year(self):
		"""The household's yearly concealment and the state's forgetting of its refusals (as `demand_year` does for other actors)."""
		seat = self.seat
		settled = {"concealed": 0.0, "cost": 0.0, "seized": 0.0, "found": 0.0}
		if seat.demand_stance == demand_answer.CONCEAL or seat.concealed > 0.0:
			draw = self.needs.legacy_dice().random()
			settled = demand_answer.settle_concealment(seat.demand_stance, max(0.0, self.needs.acting_balance()), self.state_reach(),
			                                           seat.protection, draw)
			if settled["cost"] > 0.0:
				self.needs.send(PayEdge(edges.EDGE_OFFICIALS, settled["cost"], "concealing wealth"))
			if settled["seized"] > 0.0:
				self.needs.send(TakeFromHouseholdPurse(self.needs.state_treasury().actor_id, settled["seized"], "wealth found hidden"))
				self.needs.send(RecordEvent.of("hidden_wealth_found", "The state found wealth you had hidden and took it with a penalty"))
			seat.concealed = settled["concealed"]
		if seat.defiance > 0.0:
			seat.defiance = demand_answer.defiance_fading(seat.defiance)
		return settled

	def set_household_stance(self, stance, service=0.0):
		"""Answer the state's demands by `stance` from now on, offering `service` (money's worth) when negotiating; says what
		the answer risks."""
		stance = demand_answer.checked_stance(stance)
		seat = self.seat
		seat.demand_stance = stance
		seat.service_offer = max(0.0, float(service))
		return state_demand.describe_stance(stance, self.state_reach(), seat.protection, seat.service_offer)
