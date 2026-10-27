"""Complaint 190: a one-off transfer to the state moves money from the household to the treasury, by the `pay` command and by a finished
work that declares `transfer`, and the state takes its share of one concern's takings. Each method runs on the polity module over plain
values, with the payment itself (`pay_state`) a recorder; the data declarations and typed lines are test_complaint_190_transfers."""

QUICK_TOPIC = True

from .harness import check

from sim.polity.api import CarryOutTransfers
from sim.polity import rules
from sim.refusal import cause_of, facts_of
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, polity_host
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.tests.ui_stand_in import FactViews


class Purse:
    """The household's purse a payment draws from."""

    def __init__(self, capital):
        self.capital = capital


def state(capital=1000.0, debt=0.0, claims=0.0, per_hour=2.0, specs=None):
    """The polity module over a purse, the state's debt and claims, and a pay_state that records."""
    purse = Purse(capital)
    names = {"work": {"name": "A work"}, "house": {"name": "Gambling house"}}
    module = polity_host.build(acting_balance=lambda: purse.capital, money_per_labour_hour=per_hour, output_factor=0.5,
                               tree=lambda node_id: names[node_id], mechanic=lambda name: specs or {})
    module.paid = []

    def pay_state(amount, purpose):
        module.paid.append((amount, purpose))
        purse.capital -= amount
    module.pay_state = pay_state
    module.state_debt = lambda: debt
    module.state_claims = lambda: claims
    return module


def events(module):
    return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]


# ---- what a transfer is sized by
game = state(debt=5000.0, claims=700.0)
check("a transfer of the debt is the whole debt", game.transfer_size({"of": "debt"}) == 5000.0, None)
check("a transfer of a share of the debt is that share", game.transfer_size({"of": "debt", "share": 0.25}) == 1250.0, None)
check("a transfer of the claims is the claims", game.transfer_size({"of": "claims"}) == 700.0, None)
check("a stated sum is labour hours priced in the society's coin", game.transfer_size({"labour_hours": 100.0}) == 200.0, None)
check("the sizing rule alone gives the same figures", rules.transfer_size({"of": "claims", "share": 0.5}, 5000.0, 700.0, 2.0) == 350.0, None)

# ---- paying the state out of the purse
game = state(capital=1200.0)
check("the state is paid what is wanted from the purse", game.pay_state_sum(500.0, "gift") == 500.0 and game.paid == [(500.0, "gift")], game.paid)
game = state(capital=1200.0)
check("a household that cannot cover it pays what it has and no more", game.pay_state_sum(5000.0, "debt") == 1200.0 and game.paid == [(1200.0, "debt")], game.paid)
game = state(capital=0.0)
check("an empty purse pays nothing and the state is not paid into debt", game.pay_state_sum(5000.0, "debt") == 0.0 and game.paid == [], game.paid)
game = state(capital=100.0)
check("a negative sum pays nothing", game.pay_state_sum(-5.0, "gift") == 0.0 and game.paid == [], game.paid)

# ---- settling with the state
game = state(capital=9000.0, debt=5000.0)
paid, text = game.settle_with_state("debt")
check("settling the debt pays what the state owed under that purpose", paid == 5000.0 and game.paid == [(5000.0, "debt")], game.paid)
game = state(capital=9000.0, debt=0.0)
paid, text = game.settle_with_state("debt")
check("a state that owes nothing is not paid for nothing", paid == 0.0 and game.paid == [], text)
game = state(capital=9000.0, claims=700.0)
paid, text = game.settle_with_state("claims")
check("settling the claims pays them under that purpose", paid == 700.0 and game.paid == [(700.0, "claims")], game.paid)
game = state(capital=9000.0, debt=1000.0)
paid, text = game.settle_with_state(None, 4000.0)
check("a stated sum is paid as a gift, past the debt too", paid == 4000.0 and game.paid == [(4000.0, "gift")], game.paid)
game = state(capital=9000.0)
paid, text = game.settle_with_state(None)
check("no sum and no target pays nothing", paid == 0.0 and game.paid == [], text)
game = state(capital=0.0, debt=100.0)
paid, text = game.settle_with_state("debt")
check("an empty purse pays nothing", paid == 0.0 and game.paid == [], text)
game = state(capital=9000.0, debt=5000.0)

# ---- a work that declares a transfer pays when finished
game = state(capital=9000.0, debt=8000.0, specs={"work": {"of": "debt", "purpose": "redeem"}})
game.carry_out_transfers("work")
line = events(game)[-1]
check("finishing the work pays the state the sum the spec asks, under its purpose", game.paid == [(8000.0, "redeem")], game.paid)
check("the log line says what was paid, by its kind and facts", line.kind == "state_paid" and line.facts["paid"] == 8000.0 and line.facts["work"] == "work", line)
game = state(capital=9000.0, debt=8000.0)
game.transfers_command(CarryOutTransfers("work"))
check("a work that declares no transfer pays nothing", game.paid == [] and events(game) == [], None)


# ---- the pay command
class Commander(FactViews):
    """A game that answers `settle_with_state` with what it asked."""

    capital = 1000.0

    def __init__(self, debt):
        self.debt = debt

    def state_debt(self):
        return self.debt

    def settle_with_state(self, target, amount=None):
        self.asked = (target, amount)
        return (100.0, "paid") if self.debt else (0.0, "the state owes nothing")


handlers = command_registry.handlers()
game = Commander(100.0)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, None)
check("`pay debt` settles the debt and says how much", reply["ok"] and reply["paid"] == 100.0 and game.asked == ("debt", None), reply)
game = Commander(0.0)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, None)
check("paying a debt that is gone is refused", reply["ok"] is False, reply)
game = Commander(100.0)
reply = handlers["pay"](game, {}, {"cmd": "pay"}, None)
check("`pay` with nothing named is refused and settles nothing", reply["ok"] is False and not hasattr(game, "asked"), reply)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, "the run is over")
check("a run that has ended pays nothing", reply["ok"] is False and not hasattr(game, "asked"), reply)


# ---- the state's share of one concern's takings
def levied(share=0.1, takings=1000.0, running=("house",), operating=("house",)):
    module = state()
    module.needs.running_mechanics = lambda name: [(node_id, {"share": share}) for node_id in running]
    module.needs.operating = lambda: set(operating)
    module.needs.concern_revenue = polity_host.module_harness._FakeView(lambda node_id: takings)
    return module


check("an open levied concern owes the state its share of what it earns", levied().concern_levy_due() == {"house": 0.1 * 1000.0 * 0.5}, None)
check("a concern that is not open owes nothing", levied(running=()).concern_levy_due() == {}, None)
check("a trade the society already has is not the household's concern to levy", levied(operating=()).concern_levy_due() == {}, None)
check("a concern that takes nothing owes nothing", levied(takings=0.0).concern_levy_due() == {}, None)
check("a share of nothing owes nothing", levied(share=0.0).concern_levy_due() == {}, None)
game = levied()
game.pay_concern_levies(100)
check("the levy is paid to the state for that concern", game.paid == [(50.0, "levy on house")], game.paid)
check("the first year says so in the log", len(events(game)) == 1 and events(game)[0].kind == "concern_levy", events(game))
game.pay_concern_levies(101)
check("a later year pays again and says nothing more", len(game.paid) == 2 and len(events(game)) == 1, game.paid)
