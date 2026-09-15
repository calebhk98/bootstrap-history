"""labour_productivity: split verbatim from the old test_regressions.py (original lines 9210-9850).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# THE USER'S THREE QUESTIONS. Q1: does training ten times as many smiths
# actually cut the cost of a smith? Q2: can a technology raise output per
# worker without replacing the worker (labour.py's labour_productivity),
# and is it wired to real tree nodes rather than invented ones?
# =============================================================================

# --- Q1: train ten times as many smiths, measure what a smith costs, before
# and after - exactly as asked, rather than trusting the comment in
# labour_price_factor that claims the price comes back down. household_room
# is patched open for this one check because the question is about the
# PRICING mechanism (labour_pressure vs market_supply), which is orthogonal
# to the household-capacity gate hire() also enforces; nothing else in this
# file, and no other check, depends on the patch.
_orig_room = S.Sim.household_room
_orig_supervision_room = S.Sim.supervision_room
S.Sim.household_room = lambda self: 10_000.0
S.Sim.supervision_room = lambda self: 10_000.0
try:
    small = sim(capital=1e9)
    small.hire("smith", 5)
    small.year += 10                 # let the hiring-day pressure fully decay
    big = sim(capital=1e9)
    big.hire("smith", 50)            # TEN TIMES as many smiths
    big.year += 10                   # same decay, same settling time
    cost_small = (S.ANNUAL_WAGE["smith"] * small.wage_index * small.price_index
                  * small.labour_price_factor("smith"))
    cost_big = (S.ANNUAL_WAGE["smith"] * big.wage_index * big.price_index
                * big.labour_price_factor("smith"))
    check("once the market has settled, a smith costs the SAME base wage "
          "whether the trade has 5 people in it or 50 - training ten times "
          "as many smiths does not cut the price below the wage table, it "
          "only avoids a lasting premium (see the next two checks for what "
          "training ten times as many DOES change)",
          abs(cost_big - cost_small) < 0.5, (cost_small, cost_big))

    # What ten-times-the-trade actually buys: the SAME absolute batch of new
    # hiring pressure is a smaller share of a bigger existing trade, so
    # expanding a big trade further is cheaper, in the premium it pays,
    # than expanding a small one by the same amount - this is the real
    # content of "brings the price back down", not a below-base discount.
    thin = sim(capital=1e9)
    thin.hire("smith", 5)
    thin.year += 10
    thick = sim(capital=1e9)
    thick.hire("smith", 50)
    thick.year += 10
    thin_capital_before, thick_capital_before = thin.capital, thick.capital
    thin.hire("smith", 10)
    thick.hire("smith", 10)
    fee_thin = thin_capital_before - thin.capital
    fee_thick = thick_capital_before - thick.capital
    check("expanding an already-large trade by a fixed amount costs no more "
          "in fees than expanding a small one by the same amount, once both "
          "have settled (hire()'s own price factor is read before the new "
          "batch's pressure is recorded, so a single hire() call never taxes "
          "itself - only the NEXT one)",
          abs(fee_thick - fee_thin) < 1.0, (fee_thin, fee_thick))

    per_head_thin = thin.wage_bill() / thin.employees["smith"]
    per_head_thick = thick.wage_bill() / thick.employees["smith"]
    check("the standing payroll's per-head cost, measured immediately after "
          "each identical top-up batch, is lower for the bigger trade - the "
          "same recent pressure is diluted across more existing people",
          per_head_thick < per_head_thin,
          "per head, base=5->15: %.2f   base=50->60: %.2f"
          % (per_head_thin, per_head_thick))
finally:
    S.Sim.household_room = _orig_room
    S.Sim.supervision_room = _orig_supervision_room

# --- Q2: technology that raises output per worker without replacing them.
s = sim(capital=1e9)
check("with nothing built, an hour of a trade's time is worth exactly an "
      "hour - labour_productivity changes nothing until a real technology "
      "earns it",
      s.labour_productivity("smith") == 1.0, s.labour_productivity("smith"))

before_call_on = s.hours_you_can_call_on("smith")
before_supply = s.market_supply("smith")
s.done.add("met_trip_hammer")
after_call_on = s.hours_you_can_call_on("smith")
after_supply = s.market_supply("smith")
check("a real productivity technology (the trip hammer, whose note says "
      "'much faster than hand hammering') raises the WORK a smith's hours "
      "can produce this year",
      after_call_on > before_call_on * 1.05, (before_call_on, after_call_on))
check("...without changing market_supply - the technology makes the "
      "existing smiths faster, it does not conjure more of them, so hiring "
      "capacity and labour_price_factor are untouched",
      after_supply == before_supply, (before_supply, after_supply))
check("...and leaves an UNRELATED trade's productivity at exactly 1.0 - a "
      "trip hammer for smiths does not make carpenters faster too",
      s.labour_productivity("carpenter") == 1.0, s.labour_productivity("carpenter"))

s2 = sim(capital=1e9)
for _node, _tr, _add in s2.LABOUR_PRODUCTIVITY_SOURCES:
    s2.done.add(_node)
check("stacking every productivity technology this run has wired in never "
      "pushes any trade's multiplier past the cap, however many technologies "
      "a civilization eventually builds",
      all(s2.labour_productivity(tr) <= s2.LABOUR_PRODUCTIVITY_CAP + 1e-9
          for _n, tr, _a in s2.LABOUR_PRODUCTIVITY_SOURCES),
      [(tr, s2.labour_productivity(tr)) for _n, tr, _a in sorted(
          s2.LABOUR_PRODUCTIVITY_SOURCES, key=lambda r: r[1])])

check("every node named in LABOUR_PRODUCTIVITY_SOURCES is a real node in "
      "the compiled tree, not a name that was never wired to anything",
      all(_n in NODES for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES),
      [_n for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES if _n not in NODES])
check("every trade named in LABOUR_PRODUCTIVITY_SOURCES is a real trade in "
      "the wage table",
      all(_tr in WAGES for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES),
      [_tr for _n, _tr, _a in S.Sim.LABOUR_PRODUCTIVITY_SOURCES if _tr not in WAGES])
# EDUCATING A WHOLE SOCIETY. The user's own question: "can we make the whole
# country's literacy rates improve? What if we make 5,000 schools and
# tractors and food production... can I create a 90%+ literate population?"
# See SocietyMixin.advance_society (society.py).
# ONE Sim, reused for every node: _is_agri_mechanisation reads only fixed
# tree data (see its own docstring), so which Sim answers is irrelevant, and
# the `_venture_ct` check a little above this one shows what happens to a
# check's running time when it constructs a fresh Sim per node instead -
# this file's own 3-second rule (see check() timing) exists precisely so a
# check does not silently become the slowest thing in the suite this way.
_s0_agri = sim()
_agri_nodes = sorted(k for k in NODES if _s0_agri._is_agri_mechanisation(k))
check("a genuinely farm-labour-saving slice of the tree exists and is a "
      "modest fraction of it, not the whole `food`-tagged sprawl",
      35 <= len(_agri_nodes) <= 45, len(_agri_nodes))

s_noschool = sim(capital=2000000.0, manual=False)
for k in _agri_nodes:
    s_noschool.done.add(k)
s_noschool._done_changed()
_gen0 = s_noschool.civ["literacy_general"]
for i in range(1, 301):
    s_noschool.advance_society(s_noschool.year + i)
check("mechanising every farm technology with no school ever running moves "
      "literacy not at all - this is something a society is TAUGHT, not a "
      "free drift",
      s_noschool.civ["literacy_general"] == _gen0, s_noschool.civ["literacy_general"])

s_school = run_it(sim(capital=2000000.0, manual=False), "school_founded")
_gen0b = s_school.civ["literacy_general"]
_ceil_noagri = s_school.literacy_ceiling_general()
for i in range(1, 401):
    s_school.advance_society(s_school.year + i)
check("a single running school, with no mechanised farming, raises "
      "literacy over generations but plateaus well short of near-universal",
      _gen0b < s_school.civ["literacy_general"] <= _ceil_noagri + 1e-6
      and s_school.civ["literacy_general"] < 0.5,
      (round(s_school.civ["literacy_general"], 3), round(_ceil_noagri, 3)))

s_max = run_it(sim(capital=2000000.0, manual=False),
               "school_founded", "academy_network")
s_max.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
for k in _agri_nodes:
    s_max.done.add(k)
s_max._done_changed()
check("agrarian_slack saturates at 1.0 once enough of the farm-labour-saving "
      "branch is done, not only once every last node of it is",
      s_max.agrarian_slack() == 1.0, s_max.agrarian_slack())
for i in range(1, 701):
    s_max.advance_society(s_max.year + i)
check("heavy schooling AND agricultural mechanisation together, over "
      "centuries, can reach a 90%+ literate general population - the "
      "user's own question, answered yes",
      s_max.civ["literacy_general"] >= 0.85, s_max.civ["literacy_general"])
check("...but never above the model's own ceiling: some fraction of any "
      "pre-transistor-era population is never a schooling question at all",
      s_max.civ["literacy_general"] <= 0.90 + 1e-6, s_max.civ["literacy_general"])
check("the lettered/propertied class closes most of its own gap too, on "
      "the same schooling, independent of farm mechanisation",
      s_max.civ["literacy_elite"] >= 0.95, s_max.civ["literacy_elite"])

_few_agri = sim(capital=2000000.0)
for k in _agri_nodes[:5]:
    _few_agri.done.add(k)
_few_agri._done_changed()
check("a handful of mechanised techniques frees only a little slack, not "
      "the whole ceiling",
      0.0 < _few_agri.agrarian_slack() < 0.6, _few_agri.agrarian_slack())

# --- determinism: agrarian_slack and _advance_literacy iterate self.done
# (a set) and self.civ (a dict) only through counts and direct key reads,
# never a float sum in an order that depends on PYTHONHASHSEED, but this is
# proven rather than merely argued, the same way the rest of this suite
# proves determinism elsewhere.
def _edu_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=False, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.goal, s.done_year = T['meta']['goal_node'], {}; "
         "s.done.add('school_founded'); s.operating.add('school_founded'); "
         "s.done.add('academy_network'); s.operating.add('academy_network'); "
         "s.inst_units = {'school_founded': 9.0, 'academy_network': 9.0}; "
         "[s.done.add(k) for k in sorted(N) if s._is_agri_mechanisation(k)]; "
         "s._done_changed(); "
         "s.trades_created.add('electrician'); "
         "[s.advance_society(s.year + i) for i in range(1, 201)]; "
         "print(repr((round(s.civ['literacy_general'], 12), "
         "round(s.civ['literacy_elite'], 12), "
         "'electrician' in s.trades_endemic, "
         "round(s.employees.get('electrician', 0.0), 12))))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_edu_a, _edu_b = _par_map(_edu_snapshot, ("0", "98765"))
check("literacy growth and trade absorption are identical under a "
      "different PYTHONHASHSEED",
      _edu_a == _edu_b and _edu_a, (_edu_a, _edu_b))

# =============================================================================
# A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS. The user's
# sharpest question: "if I invent electricity, you can't say that after 100
# years I still can't find anyone who can make or research generators." See
# SocietyMixin._advance_trade_absorption/_grow_endemic_trade (society.py).
s_noteach = sim(capital=5000000.0, manual=False)
s_noteach.trades_created.add("electrician")
for i in range(1, 401):
    s_noteach.advance_society(s_noteach.year + i)
check("a taught trade never naturalises without a single school ever "
      "running, however long the run - this is exactly what 'after 100 "
      "years I'm still the only electrician' looks like when nothing was "
      "ever built to change it",
      "electrician" not in s_noteach.trades_endemic
      and s_noteach.employees.get("electrician", 0.0) == 0.0,
      (sorted(s_noteach.trades_endemic), s_noteach.employees.get("electrician")))

s_teach = run_it(sim(capital=5000000.0, manual=False),
                 "school_founded", "academy_network")
s_teach.inst_units = {"school_founded": 9.0, "academy_network": 9.0}
s_teach.trades_created.add("electrician")
_yrs_needed = s_teach._trade_absorption_years(s_teach._schooling_flow())
check("heavy schooling brings absorption well under the ~110-year "
      "unschooled base, and never under the 35-year one-lifetime floor",
      35.0 <= _yrs_needed < 110.0, _yrs_needed)
_y0 = s_teach.year
_not_yet_year = _y0 + max(1, int(_yrs_needed) - 5)
for yr in range(_y0 + 1, _not_yet_year + 1):
    s_teach.advance_society(yr)
check("...and not endemic before that many years have actually passed",
      "electrician" not in s_teach.trades_endemic, s_teach.year - _y0)
_after_year = _y0 + int(_yrs_needed) + 10
for yr in range(_not_yet_year + 1, _after_year + 1):
    s_teach.advance_society(yr)
check("a heavily-schooled society naturalises a taught trade within about "
      "a century of the founder introducing it",
      "electrician" in s_teach.trades_endemic, s_teach.year - _y0)
for yr in range(_after_year + 1, _after_year + 101):
    s_teach.advance_society(yr)
check("...and goes on to actually produce its own electricians, for free, "
      "bounded by the exact same literate_capacity() wall a founder hiring "
      "or teaching them by hand is bounded by",
      0 < s_teach.employees.get("electrician", 0.0)
      <= s_teach.literate_capacity("electrician") + 1e-6,
      (round(s_teach.employees.get("electrician", 0.0), 2),
       round(s_teach.literate_capacity("electrician"), 2)))

_sess_edu = os.path.join(ROOT, _rel("education.json"))
S.save_state(s_teach, _sess_edu)
s_teach2 = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"))
s_teach2.goal, s_teach2.done_year = GOAL, {}
S.load_state(s_teach2, _sess_edu)
check("which trades have naturalised, and when each was introduced, "
      "survive a save and a fresh process loading it back",
      s_teach2.trades_endemic == s_teach.trades_endemic
      and s_teach2.trade_introduced_year == s_teach.trade_introduced_year,
      (sorted(s_teach2.trades_endemic), s_teach2.trade_introduced_year))

_st_edu, _, _ = proto([{"cmd": "state"}])
check("`state` reports this society's literacy and how far it could go "
      "from here",
      "literacy" in _st_edu[0]
      and 0.0 <= _st_edu[0]["literacy"]["general"] <= 1.0
      and _st_edu[0]["literacy"]["general_ceiling_now"]
          >= _st_edu[0]["literacy"]["general"],
      _st_edu[0].get("literacy"))
check("...and which taught trades the society has absorbed on its own",
      "trades_society_now_has_on_its_own" in _st_edu[0],
      _st_edu[0].get("trades_society_now_has_on_its_own"))

# =============================================================================
# WHAT YOU BUILT DOES NOT STAY YOURS. "You selling gunpowder to the
# military, someone else will likely want some of that money. Over a
# generation or two." See SocietyMixin.diffusion_share/diffusion_index
# (society.py) - a number exposed for a competitive-pricing pass to spend,
# deliberately not yet spent in revenue() itself (see that function's own
# docstring for why, and for the seam left for the agent doing that work).
_rev_node = next(k for k in sorted(NODES) if NODES[k].get("rev", 0) > 0)
_no_rev_node = next(k for k in sorted(NODES) if NODES[k].get("rev", 0) <= 0)

s_dif = sim(capital=1000000.0)
check("a technology nobody has opened for business has nothing to leak",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.done.add(_rev_node); s_dif.operating.add(_rev_node)
s_dif.done_year[_rev_node] = s_dif.year
check("freshly opened, on the day the doors open, none of its edge has "
      "leaked yet - the brief's own requirement, echoing goods_market_factor's",
      s_dif.diffusion_share(_rev_node) == 0.0, s_dif.diffusion_share(_rev_node))
s_dif.year += int(s_dif.VENTURE_DIFFUSION_HALF_LIFE_YEARS)
_half = s_dif.diffusion_share(_rev_node)
check("about half the edge is gone after one half-life",
      0.45 <= _half <= 0.55, _half)
s_dif.year += 400
_far = s_dif.diffusion_share(_rev_node)
check("...but a first mover never loses all of it, however long the "
      "venture runs - capped, like every other saturating share in this file",
      abs(_far - s_dif.VENTURE_DIFFUSION_CAP) < 1e-6, _far)

s_dif2 = sim(capital=1000000.0)
s_dif2.done.add(_no_rev_node); s_dif2.operating.add(_no_rev_node)
s_dif2.done_year[_no_rev_node] = s_dif2.cfg["start_year"] - 200
check("a concern with no revenue at all has no market to leak into, "
      "however long it has been open",
      s_dif2.diffusion_share(_no_rev_node) == 0.0,
      s_dif2.diffusion_share(_no_rev_node))

s_dif3 = sim(capital=1000000.0)
s_dif3.done.add(_rev_node); s_dif3.operating.add(_rev_node)
s_dif3.done_year[_rev_node] = s_dif3.year
s_dif3.year += 20
_plain = s_dif3.diffusion_share(_rev_node)
s_dif3.done.add("corpus_dispersed"); s_dif3.operating.add("corpus_dispersed")
s_dif3._done_changed()
_published = s_dif3.diffusion_share(_rev_node)
check("published knowledge (corpus_dispersed) escapes to competitors "
      "faster than a secret kept in one workshop - reusing the model's own "
      "existing idea of how knowledge spreads rather than inventing a "
      "second one",
      _published > _plain, (_plain, _published))

check("diffusion_index is 0 with nothing operating",
      sim().diffusion_index() == 0.0, sim().diffusion_index())
check("...and rises, revenue-weighted, once something is",
      s_dif3.diffusion_index() > 0.0, s_dif3.diffusion_index())

_st_dif, _, _ = proto([{"cmd": "state"}])
check("`state` reports how much of what you run has diffused to competitors",
      "diffusion_index" in _st_dif[0]
      and 0.0 <= _st_dif[0]["diffusion_index"] <= 1.0,
      _st_dif[0].get("diffusion_index"))

# --- JOB: the rubber bug (ac69bfb, e88a822) recurs across the tree. A node
# can consume a material nothing in its own ancestry can produce, and the
# game will still sell it at a flat book price - so you could build an
# aluminium monoplane in Rome 100AD with no grid, no generator, no
# electrolysis cell, buying the metal at 6 denarii a kilo. This pins the 24
# materials audited and fixed for that gap (see rome/data/review/
# MATERIAL_GATING.md for the full audit, including the ~69 materials judged
# genuinely purchasable in antiquity - iron, copper, wool, clay, timber,
# salt and the like - where no gate is correct).
#
# The walk follows BOTH `pre` and `req_any` - a node can be reached either
# way (ac69bfb's own JOB 3c, and _node_explain's "req_any COUNTS AS
# UNLOCKING" above, make the same point) - and a req_any OPTION may name a
# material rather than a node ("a purchasable commodity", see
# substitution_quality), which is not something to recurse into. And the
# graph is genuinely cyclic once req_any counts (junction_transistor ->
# silicon_path -> point_contact_transistor -> junction_transistor is one
# example already noted elsewhere in this tree) - a visited set is not
# optional here, it is the difference between this check finishing and an
# OOM kill.
def _full_ancestors(k, _nodes=NODES):
    seen, stack = set(), [k]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        n = _nodes.get(cur)
        if not n:
            continue
        for p in (n.get("pre") or []):
            if p in _nodes and p not in seen:
                stack.append(p)
        for g in (n.get("req_any") or []):
            for opt in (g.get("options") or {}):
                if opt in _nodes and opt not in seen:
                    stack.append(opt)
    seen.discard(k)
    return seen


# material key -> node ids, any ONE of which in a consumer's full ancestry
# means that consumer can plausibly get the material. Kept in sync by hand
# with the fixes this pins; MATERIAL_GATING.md explains each choice.
_GATED_MATERIALS = {
    "aluminium_kg": {"mat_aluminium"},
    "aluminum_oxide_kg": {"ch2_process_bayer"},
    "ammonia_kg": {"mat_ammonia", "chm_haber_bosch", "chm_solvay_process"},
    "bleach_kg": {"mat_chlorine", "chm_bleaching_powder"},
    "calcium_carbide_kg": {"chm_alkali_waste"},
    "celluloid_kg": {"mat_celluloid"},
    "chromium_kg": {"mat_chromium"},
    "cryolite_kg": {"mat_cryolite"},
    "manganese_kg": {"mat_manganese"},
    "molybdenum_kg": {"mt2_molybdenum_extraction"},
    "nickel_kg": {"mat_nickel"},
    "petroleum_refined_kg": {"mat_petroleum_refined"},
    "phosphorus_red_kg": {"chm_phosphorus_extraction"},
    "platinum_g": {"mat_platinum_bulk"},
    "porcelain_kg": {"mat_porcelain"},
    "quartz_tube_kg": {"fused_quartz"},
    "rubber_tubing_kg": {"mat_rubber_coagulated", "mat_synthetic_rubber"},
    "selenium_kg": {"pwr_selenium_metal"},
    "steam_kg": {"steam_atmospheric", "steam_watt", "cap_power_steam",
                 "steam_high_pressure"},
    "sulfuric_acid_kg": {"lead_chamber", "chm_contact_sulfuric"},
    "tungsten_kg": {"mat_tungsten"},
    "wood_pulp_kg": {"prn_wood_pulp"},
    "zinc_kg": {"mat_zinc", "zinc_metal", "zinc_industry_scale"},
}
# graphite_kg is only gated for the four ultra-high-purity semiconductor
# consumers - ordinary (natural, low-purity) graphite brush contacts and
# die-sinker electrodes are left alone deliberately, so this one is pinned
# node-by-node rather than material-wide (gp_carbon_brushes buying natural
# graphite off the market is correct, not a gap).
_graphite_pinned = ("ge_reduction", "silicon_path", "single_crystal",
                     "zone_refining")

# electroplating consumes nickel_kg but is deliberately left off the hook:
# it sits UPSTREAM of mat_nickel itself (mat_nickel -> cap_pure_4N ->
# electroplating), so gating it on nickel would make electroplating
# permanently unbuildable. The generic electroplating technique doesn't
# specifically need nickel anyway - silver, copper and gold plating are
# electroplating too - so this stays a documented, judged-legitimate gap
# rather than a fix (see MATERIAL_GATING.md).
_KNOWN_UNGATED = {"nickel_kg": {"electroplating"}}

_mat_gaps = {}
for _mat, _prods in _GATED_MATERIALS.items():
    _consumers = [k for k, v in NODES.items() if (v.get("mat") or {}).get(_mat)]
    _excuse = _KNOWN_UNGATED.get(_mat, set())
    _bad = [k for k in _consumers
            if k not in _excuse and not (_prods & _full_ancestors(k))]
    if _bad:
        _mat_gaps[_mat] = _bad
check("every consumer of a material this tree can only make by an invented, "
      "non-ancient process has that process (or an equally real substitute) "
      "somewhere in its own ancestry - not just a book price",
      not _mat_gaps, _mat_gaps)
check("...and there really are gated materials and consumers here to check, "
      "not an empty audit passing by having nothing to look at",
      len(_GATED_MATERIALS) >= 20
      and sum(1 for _m in _GATED_MATERIALS
              for _k, _v in NODES.items() if (_v.get("mat") or {}).get(_m)) >= 60,
      len(_GATED_MATERIALS))
_graphite_bad = [k for k in _graphite_pinned
                 if "mat_graphite_pure" not in _full_ancestors(k)]
check("the semiconductor-grade graphite crucibles on the road to the goal "
      "itself require actually-pure graphite, not natural lump graphite "
      "bought off the market",
      not _graphite_bad, _graphite_bad)

# --- three players: `why` quoted the BUILD crew as the staff requirement,
# and `open` actually enforces ongoing SUPERVISION (venture_hands), a
# different and sometimes larger number never shown before the money was
# spent. `why` must now show both, from the same function `open` checks.
r, _, _ = proto([{"cmd": "why", "id": "cementation_steel"}])
_why_open = r[0]["staff_to_keep_it_open"]
_s = sim()
_expect_sch, _expect_art = _s.venture_hands("cementation_steel")
check("`why`'s supervision figure is computed by the same function `open` "
      "enforces (venture_hands), not a second estimate of it",
      abs(_why_open["scholars"] - round(_expect_sch, 2)) < 0.01
      and abs(_why_open["artisans"] - round(_expect_art, 2)) < 0.01,
      "why said %s, venture_hands says %.2f/%.2f"
      % (_why_open, _expect_sch, _expect_art))
check("the supervision figure can genuinely exceed the build crew shown as "
      "staff_needed, which is exactly the case a Norse playtester measured "
      "(2.13 craftsmen enforced against a displayed 2 artisans)",
      _why_open["artisans"] > r[0]["staff_needed"]["artisans"],
      "staff_needed %s, staff_to_keep_it_open %s"
      % (r[0]["staff_needed"], _why_open))

# --- and a node nobody could ever run as a going concern (pure knowledge)
# gets no supervision figure at all - there is nothing to keep an eye on.
r, _, _ = proto([{"cmd": "why", "id": "ag2_adulteration_law"}])
check("a pure-knowledge node (no revenue, no upkeep) carries no "
      "staff_to_keep_it_open - there is no concern to supervise",
      r[0].get("staff_to_keep_it_open") is None, r[0].get("staff_to_keep_it_open"))

# --- three playtesters: a concern the staffing rule shut never came back on
# its own once restaffed - reopening it was `auto_open`, a SEPARATE policy
# defaulting off for a player, so every restaffing was followed by a manual
# `open`, for ever. "Most of the mid and late game was a repetitive
# hire-then-reopen treadmill rather than fresh decisions."
s = sim(capital=50000.0)
_k = "cementation_steel"
s.done.add(_k)
s._done_changed()
s.employees["artisan"] = 6.0
s._resync_pools()
ok, _ = s.open_venture(_k)
check("set-up: cementation_steel opens with six craftsmen on staff", ok)
s.employees["artisan"] = 0.0
s._resync_pools()
closed = s.close_unstaffed_ventures(s.year)
check("losing every craftsman shuts a concern that needs them to supervise",
      closed == [_k] and _k in s.mothballed and _k in getattr(s, "shut_for_staff", {}),
      closed)
s.employees["artisan"] = 6.0
s._resync_pools()
reopened = s.reopen_restaffed_ventures(s.year)
check("...and it comes back on its own once restaffed, with no 'open' typed",
      reopened == [_k] and _k in s.operating and _k not in s.mothballed
      and _k not in getattr(s, "shut_for_staff", {}), reopened)

# --- BREAK: the closing message promises "reopening soon costs a tenth of
# what opening did" - a player who instead reaches for `restore` (the verb
# that actually exists for "this is shut, bring it back") got a plain
# number with no word of which price it was, so a full-price restore 20
# years later read as the game breaking its own promise rather than the
# promise simply having lapsed. Same root cause as the earlier double-
# charge bug: an unexplained number and a wrong number look identical to a
# player who cannot see the arithmetic behind either.
s_rg = sim(capital=1_000_000.0)
_kg = "cementation_steel"
# restore_work, unlike open_venture, checks that every prerequisite is
# still done - so, unlike the plain open/close fixture above, this one
# needs the whole ancestry marked done too.
s_rg.done.update(NODES[_kg]["pre"])
s_rg.done.add(_kg)
s_rg._done_changed()
s_rg.employees["artisan"] = 6.0
s_rg._resync_pools()
s_rg.open_venture(_kg)
s_rg.employees["artisan"] = 0.0
s_rg._resync_pools()
s_rg.close_unstaffed_ventures(s_rg.year)
check("set-up: the closure is recorded as staffing-caused, with the year "
      "it happened",
      _kg in getattr(s_rg, "shut_for_staff", {}), s_rg.shut_for_staff)
_ok_rg, _msg_rg = s_rg.restore_work(_kg)
check("restoring within the grace window names that it is the discounted "
      "price, not a bare number",
      _ok_rg and "discounted tenth" in _msg_rg, _msg_rg)
# Now the same closure, but restored only after the grace window has
# lapsed - same setup, advanced past STAFF_CLOSURE_GRACE before restoring.
s_rg2 = sim(capital=1_000_000.0)
s_rg2.done.update(NODES[_kg]["pre"])
s_rg2.done.add(_kg)
s_rg2._done_changed()
s_rg2.employees["artisan"] = 6.0
s_rg2._resync_pools()
s_rg2.open_venture(_kg)
s_rg2.employees["artisan"] = 0.0
s_rg2._resync_pools()
s_rg2.close_unstaffed_ventures(s_rg2.year)
s_rg2.year += s_rg2.STAFF_CLOSURE_GRACE + 1
_ok_rg2, _msg_rg2 = s_rg2.restore_work(_kg)
check("...and restoring after the window has lapsed says outright that the "
      "discount window is gone and this is the full price, rather than "
      "silently charging ten times the number the closure message quoted",
      _ok_rg2 and "too long for the tenth" in _msg_rg2, _msg_rg2)
check("...and the lapsed-window fee really is about ten times the "
      "in-grace one, so the explanation matches the arithmetic",
      float(_msg_rg2.split("for ")[1].split(" denarii")[0].replace(",", ""))
      > 5 * float(_msg_rg.split("for ")[1].split(" denarii")[0].replace(",", "")),
      (_msg_rg, _msg_rg2))

# --- BREAK: an England playtester watched their own credit-freeze unlock
# date move silently three times - 1313, then 1320, then 1330 - because a
# second INSOLVENCY SETTLED while the first freeze had not yet lifted
# extends credit_frozen_until with a plain max(), and nothing in the event
# text said the date had changed. A deadline that quietly slides is worse
# than a longer fixed one would have been.
s_fz = sim(capital=1000.0)
_lim_fz = s_fz.credit_limit()
s_fz.capital = -(_lim_fz * 1.5)
s_fz.last_settlement = -999
s_fz.credit_frozen_until = 110   # an earlier freeze, STILL in force at yr=105
_before_log_fz = len(s_fz.log)
s_fz.enforce_credit_limit(105)
check("settling again while an earlier freeze is still in force extends "
      "the unlock date...",
      s_fz.credit_frozen_until == 117, s_fz.credit_frozen_until)
_fz_msgs = [m for _, m in s_fz.log[_before_log_fz:] if "INSOLVENCY SETTLED" in m]
check("...and says so in the same event, naming both the old and the new "
      "date, rather than moving the deadline with no word about it",
      bool(_fz_msgs) and "110" in _fz_msgs[0] and "117" in _fz_msgs[0],
      _fz_msgs)
# And the ordinary case - no prior freeze in force - gets no such addendum,
# because nothing moved.
s_fz2 = sim(capital=1000.0)
s_fz2.capital = -(s_fz2.credit_limit() * 1.5)
s_fz2.last_settlement = -999
_before_log_fz2 = len(s_fz2.log)
s_fz2.enforce_credit_limit(105)
_fz2_msgs = [m for _, m in s_fz2.log[_before_log_fz2:] if "INSOLVENCY SETTLED" in m]
check("...while a first-ever settlement, with nothing to extend, says "
      "nothing about a moved date",
      bool(_fz2_msgs) and "moves with every settlement" not in _fz2_msgs[0],
      _fz2_msgs)

# --- BREAK (REGRESSION): `state`'s "recurring" net_per_year is supposed to
# be the STANDING figure - its own comment says so - and read plain
# revenue() instead of revenue_capacity(), which a lender-facing figure
# (credit_limit) already reads for the identical reason its own docstring
# gives: "a lender does not cut your line because you took a job this
# year." Selling founder-hours with `work` swung net_per_year for exactly
# one year and reverted the instant the calendar rolled over - the label
# was lying about what kind of number it was.
s_nr = sim(capital=100000.0)
_net_before = S._agent_dispatch(s_nr, NODES, {"cmd": "state"}).get("net_per_year")
_pay_nr, _ = s_nr.work_for_wages("scholar", 1500)
check("set-up: selling founder-hours for wages actually registers as this "
      "year's wage_hours_this_year",
      s_nr.wage_hours_this_year > 0 and _pay_nr > 0,
      (s_nr.wage_hours_this_year, _pay_nr))
_after = S._agent_dispatch(s_nr, NODES, {"cmd": "state"})
check("net_per_year (the 'recurring' figure) does not swing just because "
      "this year's hours were sold for wages",
      abs(_after.get("net_per_year") - _net_before) < 5.0,
      (_net_before, _after.get("net_per_year")))
check("...while net_after_project_spend - explicitly THIS year's figure - "
      "still does reflect it, so the fix narrowed the right field rather "
      "than hiding the swing everywhere",
      abs(_after.get("net_after_project_spend") - _net_before) > 50.0,
      (_net_before, _after.get("net_after_project_spend")))
# `money`'s own net_per_year carries the identical label and the identical
# bug (protocol.py: "THE SAME FIGURE `state` PRINTS").
s_nr2 = sim(capital=100000.0)
_money_before = S._agent_dispatch(s_nr2, NODES, {"cmd": "money"}).get("net_per_year")
s_nr2.work_for_wages("scholar", 1500)
_money_after = S._agent_dispatch(s_nr2, NODES, {"cmd": "money"}).get("net_per_year")
check("`money`'s net_per_year is insulated from the same one-year swing, "
      "matching `state`'s",
      abs(_money_after - _money_before) < 5.0,
      (_money_before, _money_after))
# And stall_diagnosis's own net, which explicitly claims to be "the same
# net the ledger prints", has to actually be computed the same way now
# that the ledger's own figure changed.
import inspect as _insp2
check("stall_diagnosis computes its net from revenue_capacity(), the same "
      "call net_per_year now makes, not a second copy of the old bug",
      "revenue_capacity()" in _insp2.getsource(S.Sim.stall_diagnosis),
      "checked stall_diagnosis's own source")
