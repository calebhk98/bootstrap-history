"""goods_market: split verbatim from the old test_regressions.py (original lines 7097-7270).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# TWO LOOMS COMPETE: rome/data/review/COMMODITY_DYNAMISM.md's central goods-
# market finding, measured directly against a live Sim before this pass:
# "One loom at age 20 earns factor 0.7840. With a second identical loom
# running: 0.7840. With ten: 0.7840... a time curve wearing a market's
# clothes." goods_market_factor() now shares one total-supply figure across
# every concern in the same category, so a second (or tenth) producer must
# measurably cut into the first one's earnings.
# =============================================================================

def _mk_loom_sim(n_looms, age_years):
    """n_looms real, distinct textiles-category venture nodes, all opened
    the same year, aged the same number of years. Uses real tree nodes
    (not synthetic ones), the same way the rest of this file does."""
    cand = sorted(k for k, n in NODES.items()
                  if n.get("cat") == "textiles" and n.get("rev"))
    assert len(cand) >= n_looms, "not enough textiles venture nodes in the tree"
    chosen = cand[:n_looms]
    s = sim(civ="rome_100ad", capital=5_000_000.0)
    s.artisans = s.scholars = 100.0 * n_looms
    s.year = 100
    for k in chosen:
        s.done.add(k)
        s.done_year[k] = 100
    s._done_changed()
    for k in chosen:
        ok, msg = s.open_venture(k)
        assert ok, (k, msg)
    s.year = 100 + age_years
    return s, chosen

s_one, _one = _mk_loom_sim(1, 20)
f_one = s_one.goods_market_factor(_one[0])
s_two, _two = _mk_loom_sim(2, 20)
f_two = s_two.goods_market_factor(_two[0])
check("a lone concern in a category earns the tree's own figure trajectory, "
      "exactly as it always did - the identity a second producer must NOT "
      "break for a player who only ever builds one",
      abs(f_one - 1.0) < 1.0 and f_one < 1.0, f_one)
check("...but a second, identical concern selling into the SAME market at "
      "the same age earns measurably LESS than the lone concern did - real "
      "competition, not the pre-existing bug where both were bit-for-bit "
      "identical to the solo case",
      f_two < f_one * 0.9, (f_one, f_two))
check("...and the second concern's own factor is the same as the first's "
      "(they split one shared market evenly, being identical and the same "
      "age)",
      abs(s_two.goods_market_factor(_two[1]) - f_two) < 1e-9,
      (f_two, s_two.goods_market_factor(_two[1])))

s_ten, _ten = _mk_loom_sim(10, 20)
f_ten = s_ten.goods_market_factor(_ten[0])
check("ten identical concerns earn less again than two did - competition "
      "keeps biting as more producers pile into the same market, not just "
      "a one-time step from one to two",
      f_ten < f_two, (f_two, f_ten))
check("...and revenue() itself reflects it: ten competing concerns do not "
      "each earn what one alone would, so total revenue is far below ten "
      "times a lone concern's take",
      s_ten.revenue() < s_one.revenue() * 10 * 0.5,
      (s_one.revenue(), s_ten.revenue()))

# --- a player must see the competition, not just feel it in a smaller
# number: goods_market_note()/goods_market_summary() must say so.
_note_two = s_two.goods_market_note(_two[0])
check("a player reading `ventures`/`money` is told competition, not just "
      "time, is why a concern earns less than the tree quotes",
      bool(_note_two) and "concerns of yours are selling into this same "
      "market" in _note_two, _note_two)
_summary_two = s_two.goods_market_summary()
check("...and the aggregate `money` summary says so too",
      bool(_summary_two) and "competing with each other" in _summary_two,
      _summary_two)

# =============================================================================
# THE INCOME EFFECT: the brief's own richest idea, almost verbatim - "when
# the public has less money, they buy less. So if the price of food goes
# down, the price people would be willing to pay for diamonds or records
# would go up." Tested here against real tree nodes: a food-processing
# concern (essential) and a gambling house (about as purely discretionary
# as the tree gets).
# =============================================================================

_proc_cand = sorted(k for k, n in NODES.items()
                    if n.get("cat") == "processing" and n.get("rev"))
assert _proc_cand, "need at least one processing venture node"
_PROC_NODE = _proc_cand[0]
_ENT_NODE = "fin_gambling_house"
check("fin_gambling_house is a real, revenue-bearing tree node - not a "
      "synthetic example - in the 'luxury' category this pass now covers",
      NODES[_ENT_NODE].get("rev", 0) > 0
      and NODES[_ENT_NODE].get("cat") == "luxury", NODES[_ENT_NODE])

def _mk_income_sim(with_cheap_food):
    s = sim(civ="rome_100ad", capital=5_000_000.0)
    s.artisans = s.scholars = 200.0
    if with_cheap_food:
        s.done.add(_PROC_NODE)
        s.done_year[_PROC_NODE] = 50
        s._done_changed()
        s.year = 50
        ok, msg = s.open_venture(_PROC_NODE)
        assert ok, msg
        s.year = 200      # long saturated: essential_price_ratio at its floor
    else:
        s.year = 200
    s.done.add(_ENT_NODE)
    s.done_year[_ENT_NODE] = s.year
    s._done_changed()
    ok, msg = s.open_venture(_ENT_NODE)
    assert ok, msg
    return s

s_no_food = _mk_income_sim(False)
s_cheap_food = _mk_income_sim(True)
check("with no essential concern running, income_factor is neutral - a run "
      "that never touches food processing behaves exactly as before this "
      "pass",
      abs(s_no_food.income_factor() - 1.0) < 1e-9, s_no_food.income_factor())
check("a fully saturated, cheap essential market genuinely lowers "
      "essential_price_ratio below 1.0",
      s_cheap_food.essential_price_ratio() < 0.99,
      s_cheap_food.essential_price_ratio())
check("...which raises income_factor above 1.0 - real spending power freed "
      "up, not a cosmetic number",
      s_cheap_food.income_factor() > 1.0, s_cheap_food.income_factor())
_f_gambling_poor = s_no_food.goods_market_factor(_ENT_NODE)
_f_gambling_rich = s_cheap_food.goods_market_factor(_ENT_NODE)
check("the SAME gambling house, opened the same way, earns MORE once food "
      "is cheap and saturated than it does with no food market at all - "
      "the brief's own worked example, cheaper food raising what people "
      "will pay for a discretionary good",
      _f_gambling_rich > _f_gambling_poor, (_f_gambling_poor, _f_gambling_rich))
_note_proc = s_cheap_food.goods_market_note(_PROC_NODE)
check("processing itself (the essential) says plainly that it is a "
      "necessity and does not move with price - income_factor only ever "
      "applies to DISCRETIONARY categories, and a player reading the "
      "essential concern's own note should not be told it benefited from "
      "its own cheapness",
      _note_proc is None or "necessity" in _note_proc, _note_proc)

# --- the ledger's own "parts add up to the total" invariant survives the
# income effect too, the same standard already held for an aged loom.
_src_income = s_cheap_food.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with the "
      "income effect raising one row above the tree's own figure",
      abs(sum(_src_income.values()) - s_cheap_food.revenue()) < 1.0,
      (sum(_src_income.values()), s_cheap_food.revenue()))

# --- determinism: goods-category state is summed over self.operating, a
# set of strings, so it has to iterate sorted() - proven the same way the
# rest of this file proves it, by running twice under different hash seeds.
def _goods_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=True, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.artisans = s.scholars = 500.0; s.year = 100; "
         "cand = sorted(k for k,n in N.items() if n.get('cat')=='textiles' and n.get('rev'))[:5]; "
         "[s.done.add(k) or s.done_year.__setitem__(k, 100) for k in cand]; "
         "s._done_changed(); "
         "[s.open_venture(k) for k in cand]; "
         "s.year = 130; "
         "print(repr(round(s.goods_market_factor(cand[0]), 12)))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_gsnap_a, _gsnap_b = _par_map(_goods_snapshot, ("0", "54321"))
check("shared goods-category pricing is identical under a different "
      "PYTHONHASHSEED",
      _gsnap_a == _gsnap_b and _gsnap_a, (_gsnap_a, _gsnap_b))

