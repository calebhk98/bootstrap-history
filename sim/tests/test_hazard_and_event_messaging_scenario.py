"""Scenario (Complaint 640): a debasement stated in real terms moves no price quote a player could see. The jargon scan and
the patron cooling-off rule are in test_hazard_and_event_messaging.py.

The quote's independence from `money_real` is a rule of `project_cost`; it stays here until the quote is a function that
can be called without a game (a CONVERT-EXTRACT item of the slow-test audit).
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: a debasement announced itself and moved no price a player could see, because the model is in real terms.
s_db = sim(capital=100000.0, events=True)
# Apply one debasement shock directly. Counterfactual at the same state: the
# full quote (materials included) with the coin as debased, and with it restored.
s_db._shock_real_erosion({"name": "debasement", "real_erosion": 0.2}, 210)
_debased_price = s_db.project_cost("horse_collar")
_real_money_kept = s_db.state.economy.money_real
s_db.state.economy.money_real = 1.0
_undebased_price = s_db.project_cost("horse_collar")
s_db.state.economy.money_real = _real_money_kept
check("debasement does not move a real price quote (the model is real terms)",
      _real_money_kept < 1.0 and abs(_debased_price - _undebased_price) / _undebased_price < 1e-5,
      (_real_money_kept, _debased_price, _undebased_price))
