"""Complaint 185: money moves between actors through a ledger. The ledger's rules are tested between actors built here
(no game); the household paying the state is in test_state_payment_wiring."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRegistry, ActorsState, ledger
from sim.engine.state import ActorRecord


def ledger_balances(actor, opening=0.0):
    income = sum(actor.record.income.values())
    outlays = sum(actor.record.outlays.values())
    return abs(actor.money - (opening + income - outlays)) <= 1e-6 * max(1.0, abs(actor.money))


# ---- a transfer between any two actors conserves money (actors built here, no game)
registry = ActorRegistry(ActorsState(home_country="rome_100ad"))
treasury = registry.ensure_government("rome_100ad")
payer = registry.add("firm:payer", ActorRecord(kind="firm", money=500.0))
other = registry.add("firm:other", ActorRecord(kind="firm", money=2000.0))
ledger.transfer(other, treasury, 40.0, "requisition")
check("a transfer debits the payer and credits the payee by the same amount",
      other.money == 1960.0 and treasury.money == 40.0, (other.money, treasury.money))
ledger.transfer(payer, treasury, 100.0, "taxation")
check("a recorded payer keeps an outlay and a recorded payee an income, by purpose",
      payer.record.outlays == {"taxation": 100.0}
      and treasury.record.income == {"requisition": 40.0, "taxation": 100.0},
      (payer.record.outlays, treasury.record.income))
check("a transfer never creates or destroys money",
      abs((other.money + treasury.money + payer.money) - 2500.0) < 1e-9, (other.money, treasury.money, payer.money))
check("a recorded actor's purse is its opening money plus income less outlays",
      ledger_balances(treasury) and ledger_balances(payer, 500.0) and ledger_balances(other, 2000.0))
ledger.transfer(payer, treasury, 60.0, {"taxation": 0.5, "tithe": 0.5})
check("a payment covering several purposes books the whole amount, labelled once in the book",
      abs((payer.money + treasury.money + other.money) - 2500.0) < 1e-9 and ledger.purposes_label({"taxation": 0.5, "tithe": 0.5}) == "taxation+tithe")

