"""Money a player spends or is told about is previewed (Complaints 216, 218, 236, 248, 214). The rules that need no game are
the typed `quote` lines (the preview is asked for the same way the charge is) and the last sliver of a project's bill
(the projects module's `settle_cost_tail`, Complaint 240), called over a household that records what it pays; that a preview shows the figure the charge pays is
test_spending_quote_wiring, and the debt readings are test_start_bill_and_debt_rules."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ledger.api import NoteSpend, PayEdge
from sim.projects.constants import COST_TAIL_SETTLE_SHARE
from sim.tests import module_harness, projects_host
from sim.ui.proto.typed import parse_typed

# --- 220, 248: the typed preview lines name what they preview
check("typed 'quote hire smith 2' parses as a hire quote",
      (parse_typed("quote hire smith 2")[0] or {}).get("what") == "hire"
      and (parse_typed("quote hire smith 2")[0] or {}).get("trade") == "smith",
      parse_typed("quote hire smith 2"))
check("typed 'quote bounty <id>' parses as a bounty quote",
      (parse_typed("quote bounty fin_restaurant")[0] or {}).get("id") == "fin_restaurant",
      parse_typed("quote bounty fin_restaurant"))


# --- 240: a cash tail after the last scheduled payment settles
class Books:
    """The tail rule over a household that records what it pays."""

    def __init__(self, bill):
        self.module = projects_host.build(project_cost=lambda node_id: bill)
        self.state = SimpleNamespace(household=SimpleNamespace(total_spend=0.0))
        self.module.needs.send = self.send
        self.paid = []

    def send(self, command):
        if isinstance(command, PayEdge):
            self.paid.append((command.edge, command.amount, command.purpose))
        elif isinstance(command, NoteSpend):
            self.state.household.total_spend += command.amount

    def settle_cost_tail(self, node_id, project_state):
        return self.module.settle_cost_tail(node_id, project_state)


def owing(amount, **fields):
    return dict(cost_left=amount, spent=100.0, **fields)


books = Books(100000.0)
project = owing(40.0)
settled = books.settle_cost_tail("project", project)
check("a few cash units left after the final instalment are paid with it, so the project does not wait another year",
      settled == 40.0 and project["cost_left"] == 0.0 and project["spent"] == 140.0 and books.state.household.total_spend == 40.0
      and len(books.paid) == 1 and books.paid[0][1] == 40.0, (settled, project, books.paid))
big = owing(5000.0)
check("a remainder past the rounding share of the bill is not a tail and waits", Books(100000.0).settle_cost_tail("project", big) == 0.0
      and big["cost_left"] == 5000.0)
dust = owing(0.2)
check("less than half a unit is left alone", Books(100000.0).settle_cost_tail("project", dust) == 0.0 and dust["cost_left"] == 0.2)
starved = owing(40.0, underfunded_this_year=True)
check("a project underfunded this year pays no tail", Books(100000.0).settle_cost_tail("project", starved) == 0.0
      and starved["cost_left"] == 40.0)
edge_of_share = owing(COST_TAIL_SETTLE_SHARE * 100000.0)
check("a remainder of exactly the rounding share is a tail",
      Books(100000.0).settle_cost_tail("project", edge_of_share) == COST_TAIL_SETTLE_SHARE * 100000.0)
