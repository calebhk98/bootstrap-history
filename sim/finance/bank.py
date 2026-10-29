"""A seat founds a bank in the agent economy: its capital, in coin, comes out of its money and into the bank.

Needs: dealing_party, actor_world, mechanic, agent_economy_opened, agent_economy, year."""
from typing import Any, Dict

from sim.economy import api as economy_api
from sim.ledger.api import WithdrawHouseholdMoney
from sim.refusal import Refusal

from . import bank_rules


class Bank:

	def found_bank(self, command: Any) -> Dict[str, Any]:
		"""The acting seat puts `command.capital` of its money into a new bank."""
		needs = self.needs
		capital = command.capital
		party = needs.dealing_party()
		world = needs.actor_world()
		knows = any(party.knows(node_id, world) for node_id in needs.mechanic[bank_rules.BANKING_MECHANIC])
		refusal = bank_rules.refusal_for(knows, capital, party.money)
		if refusal is None and not needs.agent_economy_opened():
			refusal = Refusal("economy_not_open", "The economy has not opened yet.")
		if refusal is not None:
			return {"ok": False, "error": refusal, "cause": refusal.cause}
		economy = needs.agent_economy()
		units = float(capital) / economy.setup.coin_per_unit   # the capital is counted in the economy's unit
		bank = economy_api.found_bank_from_outside(economy, self.clock.acting_seat, units, needs.year(), economy_api.EDGE_EXCHANGE)
		if bank is None:
			refusal = Refusal("capital_not_positive", "Nothing went into the bank.")
			return {"ok": False, "error": refusal, "cause": refusal.cause}
		needs.send(WithdrawHouseholdMoney(float(capital)))
		return {"ok": True, "bank": bank.agent_id, "capital": float(capital),
		        "note": "Households with savings now deposit with it; its earnings above its capital are paid to you."}
