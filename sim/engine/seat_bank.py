"""A seat founds a bank: any seat whose knowledge holds a node declaring `deposit_banking` may put capital into one.

The bank is an agent of the agent economy like any a household founds (sim/economy/banks.py): it takes deposits from
households, lends them on, keeps a reserve, and can be run on. The seat's capital leaves its money and is the bank's
own capital; what the bank earns beyond that capital and the capital it keeps behind its loans is paid back to the seat.
"""
from typing import Any, Dict, Optional

from sim.refusal import Refusal

from . import economy_port_bank

BANKING_MECHANIC = "deposit_banking"


def refusal_for(knows_banking: bool, capital: Any, money: float) -> Optional[Refusal]:
    """Why the seat cannot found a bank with `capital`, or None."""
    if not knows_banking:
        return Refusal("no_banking_institution", "You do not hold a technology that lets you take deposits and lend them on; "
                       "'available' lists what you could begin.")
    if isinstance(capital, bool) or not isinstance(capital, (int, float)) or capital <= 0.0:
        return Refusal("capital_not_positive", "The capital is an amount of money above zero.", capital=capital)
    if capital > money:
        return Refusal("capital_exceeds_cash", "You hold less than that to put into a bank.", capital=capital, cash=money)
    return None


class SeatBankMixin:

    def seat_found_bank(self, capital: Any) -> Dict[str, Any]:
        """The acting seat puts `capital` of its money into a new bank."""
        party = self.dealing_party()
        world = self.view("actor_world")()
        knows = any(party.knows(node_id, world) for node_id in self.nodes_with_mechanic(BANKING_MECHANIC))
        refusal = refusal_for(knows, capital, party.money)
        if refusal is None and not self.economy.agent.opened():
            refusal = Refusal("economy_not_open", "The economy has not opened yet.")
        if refusal is not None:
            return {"ok": False, "error": refusal, "cause": refusal.cause}
        bank = economy_port_bank.found(self.economy.agent.economy(), self.state.acting_seat, float(capital), self.year)
        if bank is None:
            refusal = Refusal("capital_not_positive", "Nothing went into the bank.")
            return {"ok": False, "error": refusal, "cause": refusal.cause}
        party.money = party.money - float(capital)
        return {"ok": True, "bank": bank.agent_id, "capital": float(capital),
                "note": "Households with savings now deposit with it; its earnings above its capital are paid to you."}
