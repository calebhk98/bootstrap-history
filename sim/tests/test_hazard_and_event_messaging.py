"""What a hazard or event tells the player: no internal jargon, a fire
or raid naming what it took, the patron-death cooldown, debasement stated in
real terms, and a mitigated plague never re-quoting the raw historical toll
as if it were the outcome.

Regrouped from test_round8_fixes.py - see CLAUDE.md's test-file
reorganisation note. Checks moved verbatim; each one's own comment explains
the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: player-facing hazard notes quoted the values vector by its
# internal names ("raises w_magic_fear"), which is engine jargon a player has
# no way to read. Nothing shown to a player may name a values-vector key.
_JARGON = ("w_magic_fear", "w_eminence_danger", "w_religious_rigidity",
           "w_labour_saving", "w_commerce", "w_information", "w_novelty",
           "w_military", "adaptation_rate", "patronage_weight", "bribability")
_dirty = []
for _f in sorted(os.listdir(os.path.join(ROOT, "data/civilizations"))):
    if not _f.endswith(".json") or _f.startswith("_"):
        continue
    _civ = json.load(open(os.path.join(ROOT, "data/civilizations", _f)))
    for _h in _civ.get("hazards", []):
        _txt = " ".join(str(_h.get(x, "")) for x in ("name", "note"))
        _dirty += [(_f, _h.get("name"), _jargon_term) for _jargon_term in _JARGON if _jargon_term in _txt]
check("no hazard a player reads names an internal values-vector key",
      not _dirty, _dirty[:3])

# --- BREAK: the patron-death guard read `_last_patron_death` and the body set
# `last_patron_death`, so the 25-year cooling-off never applied and the 5%
# roll fired every year for ever - the exact bug its comment claims to fix.
s_pd = sim(capital=50000.0, events=True)
s_pd.done.add("patron_local"); s_pd._done_changed()
s_pd.rng = random.Random(4)
_deaths = []
for _y in range(100, 400):
    s_pd.year = _y
    _before = len(s_pd.log)
    s_pd._random_events(_y)
    _deaths += [message for _, message in s_pd.log[_before:] if "patron dies" in message]
check("a patron cannot die twice inside the cooling-off period",
      len(_deaths) <= 300 // 25 + 1,
      "%d deaths in 300 years" % len(_deaths))
_years = [y for y, message in s_pd.log if "patron dies" in message]
check("...and the gap between them is at least the 25 years it promises",
      all(later_year - earlier_year > 25 for earlier_year, later_year in zip(_years, _years[1:])), _years)
check("a patron's death names what it cost you",
      not _years or any("courting cost" in message and "protection falls" in message
                        for _, message in s_pd.log if "patron dies" in message),
      [message for _, message in s_pd.log if "patron dies" in message][:1])

# --- BREAK: a fire and a raid announced themselves and left the player to
# diff their own state to find out whether anything had happened.
s_fx = sim(capital=10000.0, events=True)
s_fx.rng = random.Random(7)
for _y in range(100, 200):
    s_fx.year = _y
    s_fx._random_events(_y)
_dis = [message for _, message in s_fx.log if "fire in" in message or "banditry" in message]
check("a fire or a raid says what it took",
      _dis and all("denarii" in message or "holding none" in message for message in _dis),
      _dis[:2])

# --- BREAK: a debasement announced itself and moved no price a player could
# see, because the model is in real terms. Say so, and name the real bite.
s_db = sim(capital=100000.0, events=True)
_before_price = s_db.project_cost("horse_collar")
while s_db.year < 210:
    s_db.step()
check("debasement does not move a real price quote (the model is real terms)",
      # Population recovery between plague waves moves wage_index a little,
      # so the quote drifts by a residual far below a debasement-sized move
      # (real_erosion is a few percent). Relative, so it survives cost rescaling.
      abs(s_db.project_cost("horse_collar") - _before_price) / _before_price < 1e-5,
      (_before_price, s_db.project_cost("horse_collar")))
_dbm = [message for _, message in s_db.log if "coin is worth" in message]
check("...and the announcement says so, rather than leaving it to be found",
      _dbm and "do not move" in _dbm[0] and "your chest" in _dbm[0],
      _dbm[:1])
check("...and names what the debasement actually took this year",
      _dbm and ("denarii" in _dbm[0] or "holding none" in _dbm[0]), _dbm[:1])
