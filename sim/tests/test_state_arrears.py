"""Complaint 475: collection is a modest part of the state's coin revenue; unpaid army and office pay is arrears the
state owes, paid first from later revenue, and a mutinous army takes what it is owed. A state short of its own need
lends nothing (the lending rule: test_state_surplus_rules). How a shortfall becomes arrears is
test_state_fiscal_response. The rules are called on a government and a stub world built here; what the money
screen reports the state owes is test_state_owes."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import arrears, budget_works, group_servants, revenue
from sim.agents.api import ActorRecord
from sim.agents.budget_line import Line
from sim.agents.government import Government

from .agents_fake_world import FakeWorld


class StateWorld(FakeWorld):
    """The assessments, the wage and the words a collection line and a mutiny use."""

    def __init__(self):
        super().__init__()
        self.assessments = []
        self.said = []

    def pay_per_person_year(self, trade):
        return 10.0

    def national_people(self, trade):
        return 1.0e6

    def commodity_of(self, material):
        return material

    def revenue_assessments(self):
        return self.assessments

    def money_text(self, amount, grouped=False, short=False):
        return "%.0f" % amount

    def plain_number(self, value):
        return "%.0f" % value

    def say(self, line):
        self.said.append(line)


# ---- collection is a modest part of what a form raises -----------------------------------------------------
world = StateWorld()
for basis, rate in (("harvest", 0.1), ("imports_value", 0.025)):
    base = 100000.0
    world.assessments = [revenue.Assessment("form", basis, base, rate, rate * base)]
    cost = sum(line.money for line in budget_works.collection_line(world))
    check("collecting a form on %s costs well under half of what it raises" % basis,
          0.0 < cost < 0.5 * rate * base, (cost, rate * base))

# ---- the pay the state owes ----------------------------------------------------------------------------------
owing = Government("government:home", ActorRecord(kind="government", money=0.0))
owing.record.arrears = {"army": 600.0, "administration": 300.0}
check("a state's arrears owed are the sum of what it owes its army and officials",
      owing.arrears_owed() == 900.0 and arrears.total(owing.record) == 900.0, owing.record.arrears)
check("a state that owes pay is one that cannot meet its own need", owing.cannot_meet_own_need())
square = Government("government:home", ActorRecord(kind="government", money=0.0))
check("a state that owes nothing and left nothing unpaid can", not square.cannot_meet_own_need())
lines = [Line("army", "requisition", transfer=600.0), Line("roads", "office", transfer=100.0)]
new_debt = ActorRecord(kind="government")
arrears.owe(new_debt, lines, 0.5)
check("half the army's pay unpaid is half owed, and a line that is not pay is never owed",
      new_debt.arrears == {"army": 300.0}, new_debt.arrears)

# ---- later revenue pays the arrears first ---------------------------------------------------------------------
rich = Government("government:home", ActorRecord(kind="government", money=2000.0))
rich.record.arrears = {"army": 600.0, "administration": 300.0}
paid = arrears.settle(rich, world)
check("a purse that covers the arrears pays them in full", paid == {"army": 600.0, "administration": 300.0}, paid)
check("...and nothing is owed after", arrears.total(rich.record) == 0.0 and abs(rich.money - 1100.0) < 1e-9,
      (rich.record.arrears, rich.money))
thin = Government("government:home", ActorRecord(kind="government", money=450.0))
thin.record.arrears = {"army": 600.0, "administration": 300.0}
arrears.settle(thin, world)
check("a purse that covers half pays half of each line and keeps owing the rest",
      abs(thin.record.arrears["army"] - 300.0) < 1e-9 and abs(thin.record.arrears["administration"] - 150.0) < 1e-9
      and abs(thin.money) < 1e-9, (thin.record.arrears, thin.money))
broke = Government("government:home", ActorRecord(kind="government", money=0.0))
broke.record.arrears = {"army": 600.0}
check("an empty purse pays nothing and borrows nothing", arrears.settle(broke, world) == {} and broke.money == 0.0)


# ---- the army takes its arrears --------------------------------------------------------------------------------
def army_owed(loyalty):
    """An army paid in full this year but owed a past shortfall."""
    state = Government("government:home", ActorRecord(kind="government", money=1.0e9, army=1000.0))
    state.record.need = {"army": 180000.0}
    state.record.unfunded = {"army": 0.0}
    state.record.income_reference = {group_servants.ARMY_PAY_SHARE: 1.0}
    state.record.arrears = {"army": 60000.0}
    state.record.loyalty = loyalty
    return state


mutinous = army_owed(0.0)
acted = group_servants.run_army_year(mutinous, world)
check("an army owed arrears that has lost its loyalty takes them, though this year's pay was in full",
      acted["seized"] > 0.0 and mutinous.money < 1.0e9, acted)
check("what the mutineers took is no longer owed", mutinous.record.arrears["army"] < 60000.0, mutinous.record.arrears)
loyal = army_owed(1.0)
check("an army that kept its loyalty takes nothing, whatever it is owed",
      group_servants.run_army_year(loyal, world)["seized"] == 0.0 and loyal.money == 1.0e9)
