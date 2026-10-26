"""Complaint 190: a one-off transfer to the state moves money from the household to the treasury, by the `pay` command and by a finished
work that declares `transfer`, and the state takes its share of one concern's takings. Each method runs on a stand-in `self` carrying only
what it reads, with the payment itself (`pay_state`) a recorder; the data declarations and typed lines are test_complaint_190_transfers."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.engine.concern_levy import ConcernLevyMixin
from sim.engine.transfers import TransfersMixin
from sim.refusal import cause_of, facts_of
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.tests import event_stand_in


class State:
    """A stand-in game: the household's purse, the state's debt and claims, and a pay_state that records."""
    send = event_stand_in.send

    def __init__(self, capital=1000.0, debt=0.0, claims=0.0, per_hour=2.0):
        self.state = SimpleNamespace(household=SimpleNamespace(capital=capital, log=[]), scenario=SimpleNamespace(year=100, _said_condition=set()),
                                     projects=SimpleNamespace(operating=set()))
        self.output_factor = 0.5
        self.debt, self.claims = debt, claims
        self.nodes = {"work": {"name": "A work"}, "house": {"name": "Gambling house"}}
        self.labour = SimpleNamespace(money_per_labour_hour=lambda: per_hour)
        self.paid = []
        self.specs = {}
        self.civ = {"id": "rome_100ad"}

    def pay_state(self, amount, purpose):
        self.paid.append((amount, purpose))
        self.state.household.capital -= amount

    def state_debt(self):
        return self.debt

    def state_claims(self):
        return self.claims

    def mechanic(self, node_id, name):
        return self.specs.get(node_id, {})

    def pay_state_sum(self, wanted, purpose):
        return TransfersMixin.pay_state_sum(self, wanted, purpose)

    def transfer_size(self, spec):
        return TransfersMixin.transfer_size(self, spec)


# ---- what a transfer is sized by
game = State(debt=5000.0, claims=700.0)
check("a transfer of the debt is the whole debt", TransfersMixin.transfer_size(game, {"of": "debt"}) == 5000.0, None)
check("a transfer of a share of the debt is that share", TransfersMixin.transfer_size(game, {"of": "debt", "share": 0.25}) == 1250.0, None)
check("a transfer of the claims is the claims", TransfersMixin.transfer_size(game, {"of": "claims"}) == 700.0, None)
check("a stated sum is labour hours priced in the society's coin", TransfersMixin.transfer_size(game, {"labour_hours": 100.0}) == 200.0, None)

# ---- paying the state out of the purse
game = State(capital=1200.0)
check("the state is paid what is wanted from the purse", TransfersMixin.pay_state_sum(game, 500.0, "gift") == 500.0 and game.paid == [(500.0, "gift")], game.paid)
game = State(capital=1200.0)
check("a household that cannot cover it pays what it has and no more", TransfersMixin.pay_state_sum(game, 5000.0, "debt") == 1200.0 and game.paid == [(1200.0, "debt")], game.paid)
game = State(capital=0.0)
check("an empty purse pays nothing and the state is not paid into debt", TransfersMixin.pay_state_sum(game, 5000.0, "debt") == 0.0 and game.paid == [], game.paid)
game = State(capital=100.0)
check("a negative sum pays nothing", TransfersMixin.pay_state_sum(game, -5.0, "gift") == 0.0 and game.paid == [], game.paid)

# ---- settling with the state
game = State(capital=9000.0, debt=5000.0)
paid, text = TransfersMixin.settle_with_state(game, "debt")
check("settling the debt pays what the state owed under that purpose", paid == 5000.0 and game.paid == [(5000.0, "debt")], game.paid)
game = State(capital=9000.0, debt=0.0)
paid, text = TransfersMixin.settle_with_state(game, "debt")
check("a state that owes nothing is not paid for nothing", paid == 0.0 and game.paid == [], text)
game = State(capital=9000.0, claims=700.0)
paid, text = TransfersMixin.settle_with_state(game, "claims")
check("settling the claims pays them under that purpose", paid == 700.0 and game.paid == [(700.0, "claims")], game.paid)
game = State(capital=9000.0, debt=1000.0)
paid, text = TransfersMixin.settle_with_state(game, None, 4000.0)
check("a stated sum is paid as a gift, past the debt too", paid == 4000.0 and game.paid == [(4000.0, "gift")], game.paid)
game = State(capital=9000.0)
paid, text = TransfersMixin.settle_with_state(game, None)
check("no sum and no target pays nothing", paid == 0.0 and game.paid == [], text)
game = State(capital=0.0, debt=100.0)
paid, text = TransfersMixin.settle_with_state(game, "debt")
check("an empty purse pays nothing", paid == 0.0 and game.paid == [], text)

# ---- a work that declares a transfer pays when finished
game = State(capital=9000.0, debt=8000.0)
game.specs["work"] = {"of": "debt", "purpose": "redeem"}
TransfersMixin.carry_out_transfers(game, "work")
line = game.state.household.log[-1][1]
check("finishing the work pays the state the sum the spec asks, under its purpose", game.paid == [(8000.0, "redeem")], game.paid)
check("the log line says what was paid, by its kind and facts", cause_of(line) == "state_paid" and facts_of(line)["paid"] == 8000.0 and facts_of(line)["work"] == "work", line)
game = State(capital=9000.0, debt=8000.0)
TransfersMixin.carry_out_transfers(game, "work")
check("a work that declares no transfer pays nothing", game.paid == [] and game.state.household.log == [], None)

# ---- the pay command
class Commander(State):
    def settle_with_state(self, target, amount=None):
        self.asked = (target, amount)
        return (100.0, "paid") if self.debt else (0.0, "the state owes nothing")

    @property
    def capital(self):
        return self.state.household.capital


handlers = command_registry.handlers()
game = Commander(debt=100.0)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, None)
check("`pay debt` settles the debt and says how much", reply["ok"] and reply["paid"] == 100.0 and game.asked == ("debt", None), reply)
game = Commander(debt=0.0)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, None)
check("paying a debt that is gone is refused", reply["ok"] is False, reply)
game = Commander(debt=100.0)
reply = handlers["pay"](game, {}, {"cmd": "pay"}, None)
check("`pay` with nothing named is refused and settles nothing", reply["ok"] is False and not hasattr(game, "asked"), reply)
reply = handlers["pay"](game, {}, {"cmd": "pay", "what": "debt"}, "the run is over")
check("a run that has ended pays nothing", reply["ok"] is False and not hasattr(game, "asked"), reply)

# ---- the state's share of one concern's takings
class Levied(State):
    def __init__(self, share=0.1, takings=1000.0, running=("house",)):
        super().__init__()
        self.share, self.takings, self.running = share, takings, running
        self.state.projects.operating = {"house"}

    def running_with_mechanic(self, name):
        return list(self.running)

    def mechanic(self, node_id, name):
        return {"share": self.share}

    def concern_revenue(self, node_id):
        return self.takings

    def concern_levy_due(self):
        return ConcernLevyMixin.concern_levy_due(self)


game = Levied()
check("an open levied concern owes the state its share of what it earns", ConcernLevyMixin.concern_levy_due(game) == {"house": 0.1 * 1000.0 * 0.5}, None)
game = Levied(running=())
check("a concern that is not open owes nothing", ConcernLevyMixin.concern_levy_due(game) == {}, None)
game = Levied()
game.state.projects.operating = set()
check("a trade the society already has is not the household's concern to levy", ConcernLevyMixin.concern_levy_due(game) == {}, None)
check("a concern that takes nothing owes nothing", ConcernLevyMixin.concern_levy_due(Levied(takings=0.0)) == {}, None)
check("a share of nothing owes nothing", ConcernLevyMixin.concern_levy_due(Levied(share=0.0)) == {}, None)
game = Levied()
ConcernLevyMixin.pay_concern_levies(game, 100)
check("the levy is paid to the state for that concern", game.paid == [(50.0, "levy on house")], game.paid)
check("the first year says so in the log", len(game.state.household.log) == 1 and cause_of(game.state.household.log[0][1]) == "concern_levy", game.state.household.log)
ConcernLevyMixin.pay_concern_levies(game, 101)
check("a later year pays again and says nothing more", len(game.paid) == 2 and len(game.state.household.log) == 1, game.paid)
