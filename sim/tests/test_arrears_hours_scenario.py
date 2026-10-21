"""SCENARIO (Complaint 640): a household in arrears keeps the hours of a project that owes nothing further, through the
yearly step. The funding rule is called on built inputs in test_arrears_hours."""
from .harness import *  # noqa: F401,F403

# --- scenario: a fully-paid project makes real hour progress through the yearly step while the household is in arrears
s_af = sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
             if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
# Injected directly into `active`, bypassing prerequisite legality: the allocation is under test, not the gate.
s_af.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0,
                          spent=s_af.project_cost(_af_k), cost_left=0.0,
                          lab_left=dict(_af_n["lab"]))
# In arrears by a denarius: the rule reads only whether capital is below zero, and how deep the purse goes is the
# funding rule's (tested above on a purse of any depth). A deeper debt is not clear of the limit once the project's
# hours are committed, because a founder's standing income, and with it the credit line, shrinks by them.
s_af.capital = -1.0
_in_arrears_clear_of_limit = s_af.capital < 0.0 and s_af.active[_af_k]["cost_left"] == 0.0
_ph_before_af = s_af.active[_af_k]["ph_left"]
s_af.step()
check("scenario: a fully-paid project still makes real hour progress through the year while the household is in "
      "arrears, and is not marked underfunded",
      _in_arrears_clear_of_limit and _af_k in s_af.active
      and s_af.active[_af_k]["ph_left"] < _ph_before_af - 100
      and not s_af.active[_af_k].get("underfunded_this_year"),
      (_in_arrears_clear_of_limit, _ph_before_af, s_af.active.get(_af_k, {}).get("ph_left"),
       s_af.active.get(_af_k, {}).get("why_underfunded")))
