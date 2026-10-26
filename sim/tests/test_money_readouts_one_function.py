"""Each preview and the action it previews read one function for the amount (Complaints 261, 216, 236, 210, 240, 212): the AFFORD column
and the cannot_pay_now mark ask start_refusal, `quote train` and `train` ask the labour plan, `state` reads the sustainable debt from the
method `money` reads, and the market squeeze rows sum to the deduction. Each is called on a stand-in that writes out what it reads."""
from types import SimpleNamespace
from unittest import mock

from sim.engine.economy_absorption import MarketAbsorptionMixin
from sim.ui.proto import techtree
from sim.ui.proto.dispatch_labour import _cmd_train
from sim.ui.proto.quote_spending import _quote_train
from sim.ui.proto.state_projects import _agent_state_spend_and_net

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

# --- the AFFORD column counts the starts `start` accepts, per subject; rows `start` refuses are marked.
tree = {"a": {"cat": "material"}, "b": {"cat": "material"}, "c": {"cat": "material"}}
refusals = {"a": None, "b": "no cash", "c": None}
payer = SimpleNamespace(spending_power=lambda kind: 100.0, project_cost=lambda node_id: {"a": 5.0, "b": 9.0, "c": 7.0}[node_id],
                        start_refusal=refusals.get)
with mock.patch.object(techtree, "_subject_of", return_value="metals"):
    rows, purse = techtree._digest_subject_rows(payer, tree, ["a", "b", "c"])
check("the AFFORD column counts the startable nodes whose start_refusal is None", rows[0]["you_could_pay_for"] == 2 and rows[0]["things"] == 3, rows)
with mock.patch.object(techtree, "_brief", side_effect=lambda *args: {"id": "x"}):
    marked = {node_id: techtree._startable_row(payer, tree, node_id, False).get("cannot_pay_now") for node_id in tree}
check("a row is marked cannot_pay_now exactly when start_refusal is not None", marked == {"a": None, "b": True, "c": None}, marked)

# --- quote train states the plan's fee and wage bill, and train charges and repeats the same.
plan = {"count": 2, "fee": 120.04, "hours": 300.0}


class _Labour:
    def train_check(self, trade, count, source):
        return plan, None

    def trainee_wage_bill(self, trade, count):
        return 55.55 * count

    def train(self, trade, count, source):
        trainer.capital -= plan["fee"]
        return True, "teaching"

    def director_pool(self):
        return 500.0

    def director_hours_committed(self):
        return 100.0


trainer = SimpleNamespace(labour=_Labour(), capital=1000.0)
quote = _quote_train(trainer, {}, {"trade": "machinist", "n": 2})
reply = _cmd_train(trainer, {}, {"trade": "machinist", "n": 2}, None)
check("quote train states the plan's fee as paid_now and its wage bill", quote["paid_now"] == round(plan["fee"], 1)
      and quote["wage_bill_added_per_year"] == round(55.55 * 2, 1), quote)
check("train charges what the quote states and repeats the same wage bill",
      reply["paid_now"] == quote["paid_now"] and reply["wage_bill_added_per_year"] == quote["wage_bill_added_per_year"], (quote, reply))

# --- the state's sustainable debt is the method's figure, rounded as `money` rounds it.
debtor = SimpleNamespace(
    spend_last_year=0.0, capital=-50000.0, wages_prepaid=0.0, debt_interest_rate=lambda: 0.05, revenue=lambda: 100.0, upkeep=lambda: 10.0,
    recurring_living_cost=lambda revenue, upkeep: 20.0, mine_operating_cost=lambda: 0.0, recurring_net=lambda: 70.0,
    sustainable_debt=lambda: 1234.567, view=lambda name: (lambda: 0.0))
check("state reads sustainable_debt from the sim method, rounded to one place",
      _agent_state_spend_and_net(debtor)["sustainable_debt"] == 1234.6)

# --- the squeeze rows add up to the deduction and each names its concerns.
class _Absorbing(MarketAbsorptionMixin):
    def __init__(self):
        self.nodes = {"mill": {"cat": "textiles"}, "loom": {"cat": "textiles"}, "forge": {"cat": "metals"}}
        self.state = SimpleNamespace(economy=SimpleNamespace(output_factor=1.0))

    def ledger_concern_rows(self):
        return {"mill": 300.0, "loom": 100.0, "forge": 600.0}

    def workshop_output(self):
        return 0.0


squeeze = _Absorbing().market_absorption_by_category(250.0)
check("the category rows' lost shares sum to the deduction", abs(sum(row["lost"] for row in squeeze) - 250.0) < 1e-9, squeeze)
check("each row's lost share is its share of the nominal take, the larger first",
      [(row["category"], row["lost"]) for row in squeeze] == [("metals", 150.0), ("textiles", 100.0)], squeeze)
check("each row names its concerns, dearest first, and keeps absorbed = nominal - lost",
      squeeze[1]["concerns"] == ["mill", "loom"] and all(row["absorbed"] == round(row["nominal"] - row["lost"], 1) for row in squeeze), squeeze)
check("no deduction gives no rows", _Absorbing().market_absorption_by_category(0.0) == [])

# --- the typed words parse to a train quote.
from sim.ui.proto.typed import parse_typed
check("typed 'quote train machinist 2' parses as a train quote of that trade and number",
      (parse_typed("quote train machinist 2")[0] or {}).get("what") == "train"
      and (parse_typed("quote train machinist 2")[0] or {}).get("trade") == "machinist", parse_typed("quote train machinist 2"))
