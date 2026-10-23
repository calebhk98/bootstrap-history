"""`stuck` recommends opening a shut concern only if `open` would accept it (Complaint 219): `_stuck_shut_ventures` weighs the
refusal `open` gives and the opening charge against what the household can raise, and names the best of those that pass, else the
best of the rest and why it is blocked. Called on a stand-in game that carries each concern's earnings, running cost, refusal and
charge as numbers written here."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.refusal import Refusal
from sim.ui.proto.dispatch_inspection_stuck import _stuck_shut_ventures

# id: (yearly earnings, yearly running cost, refusal of `open`, opening charge)
CONCERNS = {
    "best_but_unstaffed": (900.0, 100.0, Refusal("supervisors_missing", "nobody free to supervise it."), 50.0),
    "good": (500.0, 100.0, None, 50.0),
    "dear_to_open": (700.0, 100.0, None, 5000.0),
    "loses": (100.0, 400.0, None, 10.0),
    "running": (800.0, 100.0, None, 10.0),
}


def game(concerns=CONCERNS, spending_power=1000.0, done=None, operating=("running",)):
    return SimpleNamespace(
        done=set(CONCERNS if done is None else done), operating=set(operating), is_venture=lambda node_id: True,
        venture_real_earnings=lambda node_id: concerns[node_id][0], venture_real_upkeep=lambda node_id: concerns[node_id][1],
        open_refusal=lambda node_id, with_advice=True: concerns[node_id][2],
        opening_fee=lambda node_id, units=None: (concerns[node_id][3], 1.0), spending_power=lambda kind: spending_power)


NODES = {}
reply = _stuck_shut_ventures(game(), NODES)
check("the concern recommended is the best of those `open` would accept and the household can pay for",
      reply["kind"] == "closed" and reply["the_best_one"] == "good" and reply["what"] == "things you built and never opened", reply)
check("a concern that open would refuse is never the recommendation, however well it earns", reply["the_best_one"] != "best_but_unstaffed")

unaffordable = _stuck_shut_ventures(game(spending_power=40.0), NODES)
check("when none can be opened the best of the rest is named with open's refusal as the cause",
      unaffordable["what"] == "things you built and cannot open yet" and unaffordable["the_best_one"] == "best_but_unstaffed"
      and unaffordable["blocked_by"] == "supervisors_missing", unaffordable)

only_dear = {key: value for key, value in CONCERNS.items() if key in ("dear_to_open", "loses")}
cash_short = _stuck_shut_ventures(game(only_dear, done=only_dear), NODES)
check("when open would accept it but the charge passes what can be raised the cause is the cash",
      cash_short["the_best_one"] == "dear_to_open" and cash_short["blocked_by"] == "cash_short", cash_short)
check("a concern that costs more than it earns is not worth recommending", "loses" not in (reply["the_best_one"], unaffordable["the_best_one"]))
check("with nothing shut and worth opening there is no reason to give", _stuck_shut_ventures(game(done={"running", "loses"}), NODES) is None)
