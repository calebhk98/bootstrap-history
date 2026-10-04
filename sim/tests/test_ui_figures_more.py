"""Complaint 95: figures for wages, state notice, epidemics and project throughput, and the
per-year `cashbook` screen that reconciles cash."""
from .harness import *  # noqa: F401,F403

from sim.ui import figures as figure_registry
from sim.ui.proto.render_cash_ledger import render_cash_ledger
from sim.ui.proto.render_figures import render_figures

NEW_FIGURES = ("wages", "state_notice", "epidemic", "project_throughput")

# renderer checks on a hand-written reply: no game
text = render_cash_ledger({"ok": True, "years": [
    {"year": 10, "open_year": False, "opening": 1000.0, "closing": 1500.0,
     "causes": [{"cause": "sales", "amount": 700.0}, {"cause": "wages", "amount": -200.0}],
     "not_itemised": 0.0},
    {"year": 11, "open_year": True, "opening": 1500.0, "closing": 1400.0,
     "causes": [{"cause": "wages", "amount": -150.0}], "not_itemised": 50.0}]})
check("cashbook lists opening, causes and closing for a closed year",
      all(word in text for word in ("opening cash", "sales", "wages", "closing cash")), text)
check("cashbook marks the open year and names what the book cannot", "open, so far" in text and "not itemised" in text, text)

listing = render_figures({"figures": [{"name": "wages", "label": "wage level", "unit": "index"}]})
check("the figures listing still renders", "wages" in listing, listing)

# handler checks on one game
played = sim(capital=1_000_000.0)
played.end_year = played.cfg["start_year"] + played.cfg["horizon_years"]
S._agent_dispatch(played, NODES, {"cmd": "step", "years": 2})

check("the new figures are registered", set(NEW_FIGURES) <= set(figure_registry.FIGURES), sorted(figure_registry.FIGURES))
for name in NEW_FIGURES:
    reply = S._agent_dispatch(played, NODES, {"cmd": "figures", "id": name})
    check("figure %s answers with a value and drivers" % name,
          reply.get("ok") and reply.get("current") is not None and "drivers" in reply, reply)
check("the wage figure is the engine's wage index",
      abs(S._agent_dispatch(played, NODES, {"cmd": "figures", "id": "wages"})["current"] - played.wage_index) < 1e-3)

ledger = S._agent_dispatch(played, NODES, {"cmd": "cashbook"})
check("cashbook answers with the open year last", ledger.get("ok") and ledger["years"][-1]["open_year"], ledger)
check("every year's cash reconciles",
      all(abs(row["closing"] - row["opening"] - sum(c["amount"] for c in row["causes"]) - row["not_itemised"]) < 1.5
          for row in ledger["years"]), ledger)
check("the open year closes at cash in hand", abs(ledger["years"][-1]["closing"] - played.capital) < 0.1, ledger)
