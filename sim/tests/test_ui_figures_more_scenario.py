"""Scenarios (Complaint 95 and 640): the `figures` and `cashbook` commands on one played game after two years. The rules
are in test_ui_figures_more."""
from .harness import *  # noqa: F401,F403

NEW_FIGURES = ("wages", "state_notice", "epidemic", "project_throughput")

played = sim(capital=1_000_000.0)
played.end_year = played.cfg["start_year"] + played.cfg["horizon_years"]
S._agent_dispatch(played, NODES, {"cmd": "step", "years": 2})

for name in NEW_FIGURES:
    reply = S._agent_dispatch(played, NODES, {"cmd": "figures", "id": name})
    check("figure %s answers with a value and drivers in a played game" % name,
          reply.get("ok") and reply.get("current") is not None and "drivers" in reply, reply)
check("the wage figure of a played game is the engine's wage index",
      abs(S._agent_dispatch(played, NODES, {"cmd": "figures", "id": "wages"})["current"] - played.wage_index) < 1e-3)

ledger = S._agent_dispatch(played, NODES, {"cmd": "cashbook"})
check("every year's cash of a played game reconciles and the open year closes at cash in hand",
      ledger.get("ok") and ledger["years"][-1]["open_year"]
      and all(abs(row["closing"] - row["opening"] - sum(c["amount"] for c in row["causes"]) - row["not_itemised"]) < 1.5
              for row in ledger["years"])
      and abs(ledger["years"][-1]["closing"] - played.capital) < 0.1, ledger)
