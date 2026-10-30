"""A seat founds a bank in the agent economy: its capital, in coin, comes out of its money and into the bank.

Needs: techniques_held, acting_balance, actor_world, mechanic, agent_economy_opened."""
from typing import Any, Dict

from sim.markets.api import FoundBankFromOutside
from sim.ledger.api import WithdrawHouseholdMoney
from sim.refusal import Refusal

from . import bank_rules


class Bank:

	def found_bank(self, command: Any) -> Dict[str, Any]:
		"""The acting seat puts `command.capital` of its money into a new bank."""
		needs = self.needs
		capital = command.capital
		world = needs.actor_world()
		held = needs.techniques_held()
		knows = any(node_id in held or node_id in world.baseline_knowledge() for node_id in needs.mechanic[bank_rules.BANKING_MECHANIC])
		refusal = bank_rules.refusal_for(knows, capital, needs.acting_balance())
		if refusal is None and not needs.agent_economy_opened():
			refusal = Refusal("economy_not_open", "The economy has not opened yet.")
		if refusal is not None:
			return {"ok": False, "error": refusal, "cause": refusal.cause}
		bank_id = needs.send(FoundBankFromOutside(float(capital)))
		if bank_id is None:
			refusal = Refusal("capital_not_positive", "Nothing went into the bank.")
			return {"ok": False, "error": refusal, "cause": refusal.cause}
		needs.send(WithdrawHouseholdMoney(float(capital)))
		return {"ok": True, "bank": bank_id, "capital": float(capital),
		        "note": "Households with savings now deposit with it; its earnings above its capital are paid to you."}
