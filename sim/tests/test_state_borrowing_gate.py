"""Complaint 316: a state borrows only once it holds the technology of public debt (a node declaring the
`state_credit` mechanic, in its own knowledge or its society's baseline). Without one it has no credit ceiling, its
shortfall menu offers no loan, and a policy that names borrowing has nothing covered by it. The rules are called on a
government and a stub world built here; the whole-game scenario is test_state_borrowing_gate_scenario."""

QUICK_TOPIC = True

from .harness import NODES, check

from sim.agents import fiscal_response
from sim.agents.api import ActorRecord
from sim.agents.budget_line import Line
from sim.agents.government import Government
from sim.agents.policy import CallbackPolicy
from sim.engine.mechanics import nodes_declaring

from .agents_fake_world import FakeWorld

DEBT_NODE = "fin_public_debt"
NEED = 1000.0


class CreditWorld(FakeWorld):
    """A country whose state earns a revenue, where a node declares the state-credit mechanic."""

    def state_revenue(self):
        return 100000.0

    def state_capacity(self):
        return 0.5

    def nodes_with_mechanic(self, mechanic):
        return (DEBT_NODE,) if mechanic == "state_credit" else ()

    def state_may_borrow(self, state):
        return any(state.knows(node_id, self) for node_id in self.nodes_with_mechanic("state_credit"))


def a_state():
    return Government("government:home", ActorRecord(kind="government", money=0.0))


def short_lines():
    return [Line("army", "requisition", transfer=NEED)]


# ---- the data: a finance node declares the mechanic, with a source ----------------------------------------------
declared = nodes_declaring(NODES, "state_credit")
check("a finance node in the tree declares the state_credit mechanic, with a source",
      bool(declared) and declared[0][0].startswith("fin_") and declared[0][1].get("source"), declared)

# ---- the credit ceiling follows the technology -------------------------------------------------------------------
world = CreditWorld()
without = a_state()
check("a state without the technology has no credit ceiling", without.credit_ceiling(world) == 0.0)
holder = a_state()
holder.knowledge.add(DEBT_NODE)
check("a state holding the technology has a ceiling it can borrow up to", holder.credit_ceiling(world) > 0.0,
      holder.credit_ceiling(world))
given = CreditWorld()
given.baseline.add(DEBT_NODE)
check("a state whose civilisation has the technology in its baseline knowledge borrows too",
      a_state().credit_ceiling(given) > 0.0)

# ---- the shortfall menu offers a loan only to a state that may borrow ---------------------------------------------
offered_without = {option.subject for option in fiscal_response.menu(without, world, short_lines(), NEED).options}
offered_with = {option.subject for option in fiscal_response.menu(holder, world, short_lines(), NEED).options}
check("a state that cannot borrow is offered no loan, and can still cut",
      fiscal_response.BORROW not in offered_without and fiscal_response.CUT in offered_without, offered_without)
check("a state that can borrow is offered a loan", fiscal_response.BORROW in offered_with, offered_with)
borrowing_policy = CallbackPolicy(lambda actor, decision: [fiscal_response.BORROW])
for state in (without, holder):
    state.decision_policy = borrowing_policy
check("a policy that names borrowing covers nothing by loan for a state that cannot",
      fiscal_response.respond(without, world, short_lines(), NEED) == {fiscal_response.CUT: NEED},
      fiscal_response.respond(without, world, short_lines(), NEED))
covered = fiscal_response.respond(holder, world, short_lines(), NEED)
check("...and the same policy borrows up to what the state's ceiling carries for one that can",
      covered.get(fiscal_response.BORROW, 0.0) == min(NEED, holder.credit_ceiling(world)), covered)
