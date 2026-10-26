"""`stuck` counts as payable exactly the starts `start` accepts, and a refusal states the rule and the amount short.
Complaint 640: both rules are called on a stand-in game that answers the few questions they ask; no game is played."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.projects_starting import StartingMixin
from sim.refusal import cause_of, facts_of
from sim.ui.proto import dispatch_inspection_stuck as dispatch_inspection

PRICE = 1000.0
LINE = 600.0


class _SameKey:
    """A keyed view whose commodity key for a material is the material's own name."""

    def __getitem__(self, material):
        return material


class StartGame(StartingMixin):
    """A game that holds a cash balance, a credit line, work in hand and a bill for each node; only the money rule is real."""

    def __init__(self, capital, owed=0.0):
        projects = SimpleNamespace(active={"in_hand": {"cost_left": owed}} if owed else {}, paid_towards={}, operating=set(),
                                   done=set(), granted=set())
        self.state = SimpleNamespace(projects=projects, household=SimpleNamespace(capital=capital, employees={}))
        self.civ = {}
        self.mine_capacity = {}
        self.done, self.active = set(), projects.active

    def project_cost(self, node_id):
        return PRICE

    def project_material_upfront_refusal(self, node_id):
        return None

    def credit_limit(self):
        return LINE

    def _stock_key(self, material):
        return material

    def _material_stock(self):
        return {}

    def view(self, name):
        return {"material_commodity": _SameKey()}[name]

    def start_reason(self, node_id):
        return (node_id != "locked", "")

    def start_refusal(self, node_id, extra_owed=0.0):
        return self._money_refusal(node_id, extra_owed)


NODES = {"cheap": {}, "locked": {}, "dear": {}}
for capital in (1000.0, 400.0, 0.0, -3000.0):
    game = StartGame(capital)
    startable, payable = dispatch_inspection._stuck_startable_and_afford(game, NODES, False)
    refused = [node_id for node_id in payable if game.start_refusal(node_id)]
    accepted = [node_id for node_id in startable if not game.start_refusal(node_id)]
    check("every start stuck calls payable is accepted by start, at capital %s" % capital, refused == [], refused)
    check("every startable thing start accepts is called payable, at capital %s" % capital, sorted(payable) == sorted(accepted),
          (payable, accepted))
    check("a node whose start is not allowed at all is not startable, at capital %s" % capital, "locked" not in startable, startable)

short_game = StartGame(-6000.0)
refusal = short_game.start_refusal("dear")
check("a start past cash and credit is refused for cash", cause_of(refusal) == "cash_short", refusal)
check("the refusal states the amount short: the bill and what is owed less what cash and credit can raise",
      abs(facts_of(refusal)["short"] - (PRICE - LINE)) < 1e-9 and facts_of(refusal)["ceiling"] == LINE, facts_of(refusal))
check("debt adds nothing to what can be raised, only positive capital and the credit line",
      StartGame(-6000.0).start_refusal("dear") is not None and StartGame(400.0).start_refusal("dear") is None)
check("work already in hand counts against the same ceiling",
      cause_of(StartGame(400.0, owed=500.0).start_refusal("dear")) == "cash_short" and StartGame(400.0, owed=0.0).start_refusal("dear") is None)
check("the refusal states the rule: cash and the credit line",  # presentation: the wording of the rule
      "short" in refusal and "credit line" in refusal, str(refusal))
