"""Scenario (Complaint 640), wording of a running game; the jargon scan and the patron cooling-off rule are in
test_hazard_and_event_messaging.py.

What a hazard or event tells the player: no internal jargon, a fire
or raid naming what it took, the patron-death cooldown, debasement stated in
real terms, and a mitigated plague never re-quoting the raw historical toll
as if it were the outcome.

Regrouped from test_round8_fixes.py - see CLAUDE.md's test-file
reorganisation note. Checks moved verbatim; each one's own comment explains
the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: a patron's death left the player to find out what it cost. The cooling-off rule is
# test_hazard_and_event_messaging.py; here the death is made certain and its notice read.
s_pd = sim(capital=50000.0, events=True)
s_pd.done.add("patron_local"); s_pd._done_changed()
s_pd.rng = random.Random(4)
s_pd.PATRON_DEATH_ANNUAL_CHANCE = 1.0
s_pd._random_events(100)
_death_notices = [message for _, message in s_pd.log if "patron dies" in message]
check("a certain patron death is announced once", len(_death_notices) == 1, _death_notices)
# presentation: the death notice says what the courting cost and that protection falls
check("a patron's death names what it cost you",
      any(("courts his heir" in message or "No money was spent" in message) and "protection falls" in message
          for message in _death_notices), _death_notices[:1])

# --- BREAK: a fire and a raid announced themselves and left the player to
# diff their own state to find out whether anything had happened.
s_fx = sim(capital=10000.0, events=True)
s_fx.rng = random.Random(7)
for _y in range(100, 200):
    s_fx.year = _y
    s_fx._random_events(_y)
_dis = [message for _, message in s_fx.log if "fire in" in message or "banditry" in message]
# presentation: the notice says what was taken in money
check("a fire or a raid says what it took",
      _dis and all("denarii" in message or "holding none" in message for message in _dis),
      _dis[:2])

# --- BREAK: a debasement announced itself and moved no price a player could
# see, because the model is in real terms. Say so, and name the real bite.
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
_dbm = [message for _, message in s_db.log if "coin is worth" in message]
# presentation: the announcement tells the player the coin's face value did not move prices
check("...and the announcement says so, rather than leaving it to be found",
      _dbm and "do not move" in _dbm[0] and "your chest" in _dbm[0],
      _dbm[:1])
# presentation: the announcement names the loss in money
check("...and names what the debasement actually took this year",
      _dbm and ("denarii" in _dbm[0] or "holding none" in _dbm[0]), _dbm[:1])
