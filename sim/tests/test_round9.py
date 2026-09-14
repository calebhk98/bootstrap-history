"""round9: split verbatim from the old test_regressions.py (original lines 4892-6062).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ======================================================================
# ROUND 9: what the two play testers of round nine found.
# ======================================================================

# --- BREAK: a sacking destroyed technologies and named none of them. A play
# tester discovered theirs decades later, when `start X` said "missing
# prerequisites: <thing you built two hundred years ago>", and rebuilt the
# chain one refusal at a time.
s_sack = sim(events=True, capital=500000.0)
for _k in list(NODES)[:400]:
    s_sack.done.add(_k)
s_sack._done_changed()
s_sack.rng = random.Random(11)
for _y in range(150, 320):
    s_sack.year = _y
    s_sack._shocks(_y)
    if getattr(s_sack, "forgotten", None):
        break
check("a sacking names the technologies it destroyed",
      any("KNOWLEDGE LOST" in m and "_" in m.split("forgotten")[-1]
          for _, m in s_sack.log),
      [m for _, m in s_sack.log if "KNOWLEDGE LOST" in m][:1])
_kr = s_sack.knowledge_risk()
check("...and `risk` lists what you have to build again",
      _kr.get("you_have_already_lost", 0) > 0
      and _kr.get("and_have_to_build_again"),
      _kr.get("you_have_already_lost"))
check("...and everything it lists really is gone from what you know",
      all(x not in s_sack.done for x in _kr["and_have_to_build_again"]),
      [x for x in _kr["and_have_to_build_again"] if x in s_sack.done])
# The hedge follows what you KNOW, not what you run: a play tester thought it
# followed `operating` because a sacking had quietly taken their corpus.
s_hg = sim(capital=500000.0)
_h0 = s_hg.knowledge_risk()["hedged_by"]
s_hg.done.add("corpus_written"); s_hg._done_changed()
_h1 = s_hg.knowledge_risk()["hedged_by"]
s_hg.open_venture("corpus_written")
_h2 = s_hg.knowledge_risk()["hedged_by"]
check("building the corpus hedges you; opening it changes nothing",
      _h0 is None and _h1 == "corpus_written" and _h2 == _h1, (_h0, _h1, _h2))

# --- BREAK: "the event reported ~92.7 people gone, but the subsequent
# payroll/headcount did not appear to fall by anything close to that
# amount." Reproduced directly against _shocks(): a sack reduced artisans,
# scholars and directors_extra and left self.employees - hired smiths,
# scribes, masons, for a developed household most of its actual headcount -
# completely untouched, while the plague family a few lines above this one
# in the same function DOES reduce employees (its own `for t in self.
# employees` loop). The number the log announced was real for the
# population it measured; it was just the wrong population - not the one
# `state`'s employees_total (the screen a player actually reads as
# "headcount") reports.
s_shg = sim(capital=500000.0)
s_shg.artisans, s_shg.scholars, s_shg.directors_extra = 20.0, 10.0, 5.0
s_shg.employees = {"smith": 40.0, "scribe": 30.0, "mason": 20.0}
# directors_extra is deliberately NOT part of this total: the announcement
# never counted it (nor does the plague family's own _people_before, a few
# lines above this hazard in the same function) even though it too is
# reduced by the event - only artisans, scholars and every hired trade are
# "your people" in the sense this message means.
_shg_total0 = s_shg.artisans + s_shg.scholars + sum(s_shg.employees.values())
_shg_emp0 = sum(s_shg.employees.values())
class _ShgZeroRNG:
    def random(self):
        return 0.0
    def sample(self, population, k):
        return list(population)[:k]
s_shg.rng = _ShgZeroRNG()
s_shg.civ = dict(s_shg.civ)
s_shg.civ["hazards"] = [{"name": "TEST SACK", "years": [s_shg.year, s_shg.year],
                         "sack_chance": 1.0}]
_before_shg = len(s_shg.log)
s_shg._shocks(s_shg.year)
_shg_msgs = [m for _, m in s_shg.log[_before_shg:] if "a site is sacked" in m]
_shg_announced = float(re.search(r"([\d.]+) of your people gone",
                                 _shg_msgs[0]).group(1)) if _shg_msgs else 0.0
_shg_total1 = s_shg.artisans + s_shg.scholars + sum(s_shg.employees.values())
check("a sack's own report of how many people are gone and the actual fall "
      "in total headcount (artisans + scholars + every hired trade) are "
      "the same number, not two that drifted apart",
      _shg_announced > 0
      and abs((_shg_total0 - _shg_total1) - _shg_announced) < 0.05,
      (_shg_announced, _shg_total0 - _shg_total1))
check("...and that headcount fall is NOT zero just because most of this "
      "household's people are hired trade staff rather than the generic "
      "artisan/scholar pools - this was the actual bug: a sack that hit "
      "everyone except whoever `employees` tracked",
      sum(s_shg.employees.values()) < _shg_emp0,
      (sum(s_shg.employees.values()), _shg_emp0))
check("...and `state`'s own employees_total - what a player rereads as "
      "payroll/headcount - reflects that same fall",
      abs(S._agent_dispatch(s_shg, NODES, {"cmd": "state"})["employees_total"]
          - sum(s_shg.employees.values())) < 1e-6,
      S._agent_dispatch(s_shg, NODES, {"cmd": "state"})["employees_total"])

# --- BREAK, the one that actually cost a run: `risk` and the sack disagreed
# about what a closed corpus is worth. `risk` read has() (fixed already, see
# the comment above it: "books that exist are books that exist") and the
# sack read running() (a going concern), so a corpus that had been built and
# since closed showed on `risk` as corpus_dispersed's 12%/8% hedge and then
# ate corpus_written's weaker 45%/22% the moment a sack actually landed - up
# to nearly three times the advertised damage. Sim.corpus_hedge() (core.py)
# is now the one place both answer from; every check below calls the real
# `knowledge_risk()` and the real `_shocks()` side by side, so this fails
# the moment either one stops asking corpus_hedge() and starts answering on
# its own again.
class _AlwaysSackRNG:
    """random() always fires the sack; sample() always takes the front of
    the (already-sorted) list, so how many are lost depends only on frac -
    never on luck."""
    def random(self):
        return 0.0
    def sample(self, population, k):
        return list(population)[:k]


def _corpus_sack_scenario(hedge_node, n_done=300):
    s = sim(capital=1_000_000.0)
    cands = sorted(k for k in NODES if NODES[k]["tier"] >= 2
                   and k not in s.granted)[:n_done]
    s.done.update(cands)
    if hedge_node:
        s.done.add(hedge_node)
    s._done_changed()
    s.rng = _AlwaysSackRNG()
    s.civ = dict(s.civ)
    s.civ["hazards"] = [{"name": "TEST SACK", "years": [s.year, s.year],
                         "sack_chance": 1.0}]
    return s


def _expected_losable(s):
    return sorted(k for k in s.done
                  if NODES[k]["tier"] >= 2 and k not in s.granted
                  and k != "corpus_dispersed")


# No corpus at all: the undefended figures.
s_f1_none = _corpus_sack_scenario(None)
_kr_none = s_f1_none.knowledge_risk()
check("no corpus built: `risk` declares the undefended 80% chance / 40% "
      "fraction",
      _kr_none["loss_chance_if_a_site_is_sacked"] == 0.80
      and _kr_none["fraction_lost_when_it_happens"] == 0.40
      and _kr_none["hedged_by"] is None, _kr_none)

# corpus_written built, but NOT operating (closed, same as the reported
# run's corpus_dispersed).
s_f1_w = _corpus_sack_scenario("corpus_written")
_kr_w = s_f1_w.knowledge_risk()
check("corpus_written, closed (not running): `risk` still credits it - "
      "has(), not running()",
      _kr_w["hedged_by"] == "corpus_written"
      and _kr_w["fraction_lost_when_it_happens"] == 0.22, _kr_w)
_losable_w = _expected_losable(s_f1_w)
s_f1_w._shocks(s_f1_w.year)
_lost_w = len(getattr(s_f1_w, "forgotten", None) or {})
check("...and the sack itself takes exactly the fraction `risk` told you "
      "to expect for a closed corpus_written (22%) - not more, not less",
      _lost_w == max(1, int(len(_losable_w) * 0.22)), (_lost_w, len(_losable_w)))

# corpus_dispersed built, but NOT operating - the exact scenario that cost
# the reported run 486 technologies instead of the roughly three times
# fewer `risk` had told them to expect.
s_f1_d = _corpus_sack_scenario("corpus_dispersed")
_kr_d = s_f1_d.knowledge_risk()
check("corpus_dispersed, closed (not running): `risk` credits the 12% "
      "chance / 8% fraction hedge",
      _kr_d["hedged_by"] == "corpus_dispersed"
      and _kr_d["fraction_lost_when_it_happens"] == 0.08, _kr_d)
_losable_d = _expected_losable(s_f1_d)
s_f1_d._shocks(s_f1_d.year)
_lost_d = len(getattr(s_f1_d, "forgotten", None) or {})
check("THE CHECK THAT FAILS IF `risk` AND THE SACK EVER DISAGREE AGAIN: a "
      "closed corpus_dispersed makes the sack take the SAME 8% `risk` "
      "declared, not corpus_written's 22%",
      _lost_d == max(1, int(len(_losable_d) * 0.08)), (_lost_d, len(_losable_d)))
check("...nearly three times less damage than a closed corpus_written "
      "sack took, matching what `risk` promised for each",
      _lost_d < _lost_w, (_lost_d, _lost_w))

# --- BREAK: dispersal is supposed to put copies beyond the reach of a
# sacking on one site; `losable` let one sacking delete corpus_dispersed
# globally, which is incoherent on its own terms - the one thing a raid on
# a single workshop cannot reach is a copy sitting in a library somewhere
# else. corpus_written - one set of books, in one place - has no such
# claim, and stays losable.
check("corpus_dispersed is never among what THIS sack forgets, across "
      "hundreds of candidates and a sack big enough to take 22% of them",
      "corpus_dispersed" not in (getattr(s_f1_d, "forgotten", None) or {}),
      getattr(s_f1_d, "forgotten", None))
for _seed in range(1, 7):
    s_f3 = sim(capital=500000.0)
    for _k in list(NODES)[:400]:
        s_f3.done.add(_k)
    s_f3.done.add("corpus_dispersed")
    s_f3._done_changed()
    s_f3.rng = random.Random(_seed)
    for _y in range(150, 320):
        s_f3.year = _y
        s_f3._shocks(_y)
    check("...holds across real (non-deterministic) sacks too, seed %d"
          % _seed,
          "corpus_dispersed" not in (getattr(s_f3, "forgotten", None) or {}),
          getattr(s_f3, "forgotten", None))
# And the converse: the exclusion is scoped to corpus_dispersed BY NAME,
# not to tier 2 in general and not to corpus_written (tier 1, and so
# already outside the sack's tier>=2 reach on its own, with or without this
# fix - one set of books in one place was never the node this mechanism
# could take either way; only corpus_dispersed's own tier made it eligible
# before this fix, and only this fix's exclusion takes it out again). A
# second, ordinary tier>=2 node sitting right next to corpus_dispersed in
# `done` is NOT spared.
s_f3w = sim(capital=500000.0)
_f3_other = next(k for k in NODES if NODES[k]["tier"] >= 2
                 and k != "corpus_dispersed" and k not in s_f3w.granted)
s_f3w.done.update(["corpus_dispersed", _f3_other])
s_f3w._done_changed()
s_f3w.rng = _AlwaysSackRNG()
s_f3w.civ = dict(s_f3w.civ)
s_f3w.civ["hazards"] = [{"name": "TEST SACK", "years": [s_f3w.year, s_f3w.year],
                         "sack_chance": 1.0}]
s_f3w._shocks(s_f3w.year)
check("an ordinary tier>=2 node sharing the sack with corpus_dispersed is "
      "the one that goes, not corpus_dispersed - the exclusion is scoped "
      "to the one node whose whole claim is dispersal, not to tier 2 at "
      "large",
      _f3_other in (getattr(s_f3w, "forgotten", None) or {})
      and "corpus_dispersed" not in (getattr(s_f3w, "forgotten", None) or {}),
      (getattr(s_f3w, "forgotten", None), _f3_other))

# --- BREAK: the KNOWLEDGE LOST line could contradict itself in the same
# breath - "the corpus was never printed and dispersed" built AFTER the
# drop had already removed corpus_dispersed from `done`, next to a clause
# that says outright "THE CORPUS ITSELF WENT". Both claims about the same
# sacking. The text must be built from how things stood BEFORE the loss.
s_f2 = sim(capital=500000.0)
s_f2.done.add("corpus_dispersed")
for _k in sorted(k for k in NODES if NODES[k]["tier"] >= 2
                 and k not in s_f2.granted and k != "corpus_dispersed")[:200]:
    s_f2.done.add(_k)
s_f2._done_changed()
s_f2.rng = _AlwaysSackRNG()
s_f2.civ = dict(s_f2.civ)
s_f2.civ["hazards"] = [{"name": "TEST SACK", "years": [s_f2.year, s_f2.year],
                        "sack_chance": 1.0}]
_before_f2 = len(s_f2.log)
s_f2._shocks(s_f2.year)
_f2_msgs = [m for _, m in s_f2.log[_before_f2:] if "KNOWLEDGE LOST" in m]
check("a sack that cannot touch corpus_dispersed (it is excluded from "
      "`losable`) never claims in the same breath that the corpus was "
      "never dispersed and that the corpus itself went",
      bool(_f2_msgs)
      and not ("never printed and dispersed" in _f2_msgs[0]
               and "CORPUS ITSELF WENT" in _f2_msgs[0]), _f2_msgs)
check("...and, since the corpus really is still dispersed, the line does "
      "not even raise the 'never dispersed' clause",
      bool(_f2_msgs) and "never printed and dispersed" not in _f2_msgs[0],
      _f2_msgs)

# --- PROVED ON A REAL PLAYER'S SAVE, not just constructed abstractly.
# rome/playtest/fixtures/rome_380_corpus_bug.json is the fixture a player
# actually reached: Rome at 380 AD, fog on, immortal, 2,049 done, 309
# million denarii, with BOTH corpus_written and corpus_dispersed done and
# NEITHER one operating - a household that wrote the corpus, dispersed it,
# and had since stopped paying to keep either scriptorium open. Before this
# fix: `risk` read has() and promised the dispersed-corpus hedge (12%/8%);
# the sack read running(), found neither corpus open, and fell all the way
# through to the UNDEFENDED branch (80%/40%) - not merely corpus_written's
# weaker figure. Against this save's exact 1,214-node losable pool that is
# 97 promised against 485 actually taken - five times the loss the screen
# said to expect, not "nearly three times" - and corpus_dispersed itself
# was destroyed in the very sack `risk` had said it hedged, producing the
# self-contradicting line Fault Two names: "the corpus was never printed
# and dispersed. THE CORPUS ITSELF WENT (corpus_dispersed)" - both about
# the one sacking. Confirmed by hand against the unfixed code (see the
# commit message for the exact before-fix log line this save produces);
# this check runs only the fixed code, deterministically, and would fail
# the moment `risk` and the sack disagree about this save again.
_FIXTURE_380 = os.path.join(ROOT, "rome", "playtest", "fixtures",
                            "rome_380_corpus_bug.json")
s_fix = sim(capital=1.0)
S.load_state(s_fix, _FIXTURE_380)
check("the fixture is what it claims to be: both corpora done, neither "
      "one operating",
      s_fix.has("corpus_written") and s_fix.has("corpus_dispersed")
      and "corpus_written" not in s_fix.operating
      and "corpus_dispersed" not in s_fix.operating,
      (s_fix.has("corpus_written"), s_fix.has("corpus_dispersed"),
       "corpus_written" in s_fix.operating, "corpus_dispersed" in s_fix.operating))
_fix_losable_before = [k for k in s_fix.done
                       if NODES[k]["tier"] >= 2 and k not in s_fix.granted]
check("...and its losable pool (done, tier>=2, not granted) really is "
      "1,214, the figure the rest of this check is measured against",
      len(_fix_losable_before) == 1214, len(_fix_losable_before))
_fix_pl, _fix_frac, _fix_hedge = s_fix.corpus_hedge()
check("Sim.corpus_hedge() - the one function that answers what THIS "
      "household's corpus is worth against a sacking - returns the "
      "dispersed-corpus figure for this exact save, because the books "
      "exist whether or not anyone is currently paid to keep printing "
      "more of them",
      _fix_hedge == "corpus_dispersed" and _fix_frac == 0.08, _fix_frac)
_fix_kr = s_fix.knowledge_risk()
check("...and `risk` reports the identical figure for this save - the "
      "two are the same call, not two answers that happen to agree today",
      _fix_kr["hedged_by"] == "corpus_dispersed"
      and _fix_kr["fraction_lost_when_it_happens"] == 0.08, _fix_kr)
s_fix.rng = _AlwaysSackRNG()
s_fix.civ = dict(s_fix.civ)
s_fix.civ["hazards"] = [{"name": "Adrianople and the Gothic settlement",
                         "years": [s_fix.year, s_fix.year], "sack_chance": 1.0}]
_before_fix_log = len(s_fix.log)
s_fix._shocks(s_fix.year)
_fix_lost = len(getattr(s_fix, "forgotten", None) or {})
_fix_msgs = [m for _, m in s_fix.log[_before_fix_log:] if "KNOWLEDGE LOST" in m]
check("THE CHECK THAT FAILS IF THE SACK AND `risk` EVER DISAGREE AGAIN, "
      "run against a real player's own save: this sack takes 97 "
      "technologies (8% of the 1,213 losable once corpus_dispersed is "
      "excluded) - the figure `risk` promised - not 267 (corpus_written's "
      "22%) and not 485 (the undefended 40% this exact save actually took "
      "before this fix, five times the loss the screen had said to "
      "expect)",
      _fix_lost == max(1, int((len(_fix_losable_before) - 1) * 0.08)) == 97,
      (_fix_lost, "expected 97 of 1213"))
check("...and the corpus that was just credited with hedging this "
      "sacking is still standing afterwards - dispersal put it beyond "
      "this one site's reach, not merely beyond this one dice roll's",
      "corpus_dispersed" in s_fix.done
      and "corpus_dispersed" not in (getattr(s_fix, "forgotten", None) or {}),
      "corpus_dispersed" in s_fix.done)
check("...and the KNOWLEDGE LOST line for this exact save no longer "
      "contains the self-contradiction a player actually read - claiming "
      "in one breath that the corpus was never dispersed and that the "
      "corpus itself just went",
      bool(_fix_msgs)
      and not ("never printed and dispersed" in _fix_msgs[0]
               and "CORPUS ITSELF WENT" in _fix_msgs[0])
      and "never printed and dispersed" not in _fix_msgs[0],
      _fix_msgs)

# --- BREAK: naming WHAT was forgotten (the fix above) is not the same as
# saying what it did to the road to the goal. A Rome player with a real goal
# set lost 22 technologies to a triple crisis - about a third of all
# critical-path progress, undone in one turn - and the KNOWLEDGE LOST line
# said nothing about the goal; they found the regression only by re-running
# `path` afterwards and comparing it by hand to what they remembered. Forced
# deterministic (random.random always 0, sample always takes the front of
# the list) so this does not depend on finding a lucky seed.
class _AlwaysZeroRNG:
    def random(self):
        return 0.0
    def sample(self, population, k):
        return list(population)[:k]
s_kr2 = sim(capital=1_000_000.0)
_gc2 = sorted(S.closure(NODES, GOAL))
_on_road_cands = [k for k in _gc2 if NODES[k]["tier"] >= 2][:6]
check("a tier>=2 node on the actual road to the goal exists to test "
      "against - this is a property of the live tree, not a fixture",
      len(_on_road_cands) >= 1, _on_road_cands)
s_kr2.done.update(_on_road_cands)
s_kr2._done_changed()
s_kr2.rng = _AlwaysZeroRNG()
s_kr2.civ = dict(s_kr2.civ)
s_kr2.civ["hazards"] = [{"name": "TEST CRISIS", "years": [s_kr2.year, s_kr2.year],
                         "sack_chance": 1.0}]
_before_kr2 = len(s_kr2.log)
s_kr2._shocks(s_kr2.year)
_kr2_msgs = [m for _, m in s_kr2.log[_before_kr2:] if "KNOWLEDGE LOST" in m]
check("the KNOWLEDGE LOST event names how many of the forgotten "
      "technologies stood on the road to the current goal, in the same "
      "breath as the loss itself",
      bool(_kr2_msgs) and "road to your goal" in _kr2_msgs[0],
      _kr2_msgs)
check("...and points at 'path' as where to see the route's new shape, "
      "rather than leaving that to be discovered by comparison",
      bool(_kr2_msgs) and "'path'" in _kr2_msgs[0], _kr2_msgs)

# --- BREAK: twenty concerns, twenty-five years, income flat, because nothing
# said on the main screen what leaving them shut was costing.
s_sh = sim(capital=50000.0)
for _k in list(NODES)[:200]:
    s_sh.done.add(_k)
s_sh._done_changed()
_stsh = S._agent_state(s_sh, NODES)
check("state says in money what your shut concerns would earn",
      _stsh.get("shut_concerns_would_earn_a_year", 0) > 0,
      _stsh.get("shut_concerns_would_earn_a_year"))
check("...and a player running everything is not nagged about it",
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year") is None,
      S._agent_state(sim(), NODES).get("shut_concerns_would_earn_a_year"))

# --- THE GENERAL CASE the corpus bug was one instance of: has() gates the
# tree and the goal, running() gates the payout, and `shut_concerns` above
# only ever covered the payout being MONEY. A player who built patron_
# imperial and then let it close keeps appearing on `available` to have
# "a patron with soldiers" - has() never stops being true - while every
# running()-gated number that patron actually paid (protection, credit,
# state funding, status - update_protection and credit_limit in society.py
# and economy.py) silently went to zero, and nothing on any screen said so
# until this.
s_cg = sim(capital=50000.0)
s_cg.done.add("patron_imperial")
s_cg.done.add("corpus_dispersed")
s_cg._done_changed()
_cg_gaps = s_cg.capability_gaps()
check("a capability institution that is done but not operating is named, "
      "by id, with the specific benefit it is not collecting right now",
      {g["id"] for g in _cg_gaps} == {"patron_imperial", "corpus_dispersed"},
      _cg_gaps)
check("the warning has the exact shape asked for: 'Critical capability "
      "completed but not operating: <id>. <benefit> is currently "
      "inactive.', with the fix command that actually reopens it",
      all(g["warning"] == ("Critical capability completed but not "
                           "operating: %s. %s is currently inactive."
                           % (g["id"], g["benefit_switched_off"]))
          and g["fix"] == "open %s" % g["id"]
          for g in _cg_gaps),
      _cg_gaps)
check("...and closes the moment the doors reopen - this is a LIVE check of "
      "running(), not a one-time note",
      (s_cg.operating.add("patron_imperial"),
       {g["id"] for g in s_cg.capability_gaps()})[1] == {"corpus_dispersed"},
      s_cg.capability_gaps())
s_cg.operating.discard("patron_imperial")
check("plague_preparedness is deliberately never warned about: its only "
      "measurable protection (HAZARD_COUNTERS) is has()-gated like corpus, "
      "so closing it costs nothing today, and a false alarm here is "
      "exactly the wall-of-text failure this feature exists to avoid",
      "plague_preparedness" not in s_cg.NOT_OPERATING_BENEFIT,
      sorted(s_cg.NOT_OPERATING_BENEFIT))
check("fin_university's sole benefit is shared (an `or`) with "
      "school_founded in update_protection, so it is only named while "
      "BOTH are closed, never while school_founded alone still covers it",
      (lambda s: (
          s.done.add("fin_university"), s.done.add("school_founded"),
          s.operating.add("school_founded"), s._done_changed(),
          "fin_university" not in {g["id"] for g in s.capability_gaps()})[-1]
      )(sim()),
      "checked fin_university/school_founded or-gate")
_st_cg = S._agent_state(s_cg, NODES)
check("`state` - the screen a player rereads every year - carries this "
      "warning too, not only a command nobody runs unprompted",
      _st_cg.get("critical_capabilities_not_operating") is not None
      and {g["id"] for g in _st_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", "patron_imperial"},
      _st_cg.get("critical_capabilities_not_operating"))
check("...and says nothing when every completed capability is open",
      S._agent_state(sim(), NODES).get(
          "critical_capabilities_not_operating") is None,
      S._agent_state(sim(), NODES).get("critical_capabilities_not_operating"))
_risk_cg = s_cg.knowledge_risk()
check("`risk` - the screen whose whole job is telling you what protects "
      "you - carries the same warning, independent of `state`",
      _risk_cg.get("critical_capabilities_not_operating") is not None
      and {g["id"] for g in _risk_cg["critical_capabilities_not_operating"]}
          == {"corpus_dispersed", "patron_imperial"},
      _risk_cg.get("critical_capabilities_not_operating"))
check("the id named is never hidden under fog - a player has always "
      "already discovered anything in their own `done`",
      all(s_cg.is_visible(g["id"]) for g in _cg_gaps), _cg_gaps)

# --- BREAK: auto_mine took 353,039 a year against 467,227 of revenue and
# there was no command that named what you owned or what it cost.
s_mn = sim(capital=2000000.0)
s_mn.open_mine("coal", 400, partial=False)
_rmn_new = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("a shaft you have just sunk is listed while it is still being sunk",
      _rmn_new["mines_you_own"] != "none"
      and _rmn_new["still_being_sunk"].get("coal"),
      _rmn_new.get("mines_you_own"))
for _ in range(int(s_mn.MINE_LEAD_YEARS) + 1):
    s_mn.year += 1
    s_mn.commission_mines()
_rmn = S._agent_dispatch(s_mn, NODES, {"cmd": "mines"})
check("there is a command that lists the mines you own and their cost",
      _rmn["mines_you_own"] != "none"
      and _rmn["they_cost_you_a_year_in_all"] > 0, _rmn.get("mines_you_own"))
check("...and each row says how to shut it",
      all("close" in r["shut_it_with"] for r in _rmn["mines_you_own"]),
      _rmn["mines_you_own"][:1])
check("...and it renders as a table, not a dict dump",
      "YOUR OWN WORKINGS" in _RP("mines", _rmn) and "{" not in _RP("mines", _rmn),
      _RP("mines", _rmn)[:60])

# --- BREAK: Han China was told it writes its corpus "in plain quantitative
# Greek and Latin" and seeks "Senatorial patronage".
for _cid, _bad in (("han_china_100ad", "Greek and Latin"),
                   ("norse_900ad", "Senatorial patronage"),
                   ("mexica_1500", "Greek and Latin"),
                   ("england_1300", "Senatorial patronage")):
    _rl, _, _ = proto([{"cmd": "why", "id": "corpus_written"},
                       {"cmd": "why", "id": "patron_senatorial"}], civ=_cid)
    check("%s is not handed Rome's own words" % _cid,
          _bad not in json.dumps(_rl), _bad)
_rr, _, _ = proto([{"cmd": "why", "id": "corpus_written"}], civ="rome_100ad")
check("...and Rome, which the tree is written from, is left alone",
      "Greek and Latin" in json.dumps(_rr), json.dumps(_rr)[:120])

# --- BREAK: "unknown_source" reached a player-facing refusal, which is data,
# not English.
s_sl = sim()
s_sl.done.update(NODES)
s_sl.done.discard("el2_potentiometer_method_measurement")
s_sl.done.discard("dynamo")
s_sl._done_changed()
_msl = s_sl.start_reason("el2_potentiometer_method_measurement")[1]
check("a substitution group reads as English, not as a data slug",
      "_" not in _msl.split("you have none")[0], _msl[:90])


# ======================================================================
# ROUND 9, the break tester: a deadlock, a silent death, and the same seed
# giving three different answers.
# ======================================================================

# --- BREAK: `--seed` did not reproduce a run. Same script, same seed, three
# runs: 587,300 / 6,664,218 / 6,652,459 in capital. PYTHONHASHSEED=0 made them
# identical. Float sums over SETS: addition is not associative, the total
# gates open_venture with a hard comparison, and one bit decides a century.
def _one_run(seed=9, years=180, civ="rome_100ad"):
    s_ = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False,
               civ=S.load_civ(civ), cfg={"start_capital": 100000.0})
    s_.goal, s_.done_year = GOAL, {}
    for _ in range(years):
        s_.step()
        if s_.dead_reason or s_.goal_year:
            break
    return (round(s_.capital, 6), len(s_.done), len(s_.operating),
            round(s_.reputation, 9))

# THE FIRST OF THESE COSTS 190 OF THE SUITE'S SECONDS, because it simulates
# 180 years. It is kept exactly as it was: it catches cross-instance state
# leaking WITHIN one process (two Sim objects built back to back in the same
# interpreter disagreeing), which is a different bug class from the second
# check below and one perf_fingerprint cannot see, because perf_fingerprint
# always runs its scenarios in the same order in the same process - it never
# builds two independent runs back to back the way this one does.
def _same_seed_same_run():
    a = _one_run()
    return _one_run() == a, (a, _one_run())

slow_check("the same seed gives the same run, twice in one process",
           _same_seed_same_run)

# THE SECOND USED TO cost 122s comparing FOUR numbers (capital, len(done),
# len(operating), reputation) at year 180, for ONE civilisation and ONE seed
# under ONE alternate hash seed. An experiment that injected a real
# "iterates an unsorted set feeding a float sum" bug (the exact class this
# check exists to catch - see ROUND 9's docstring above) measured how well
# each approach actually detects it:
#
#   this check, as it was (180 years, 1 civ, 1 seed): diverged at year 107,
#       121 or 196 depending which seed was tried, and did not diverge at
#       ALL within 200 years for 3 of 6 seeds tried - a coin flip, for the
#       one thing it exists to catch.
#   rome/sim/perf_fingerprint.py's state_of()/digest() (nine scenarios,
#       five civilisations, hashing the FULL save-file state every year):
#       diverged within 1-7 years on ALL NINE scenarios, every time.
#
# So the expensive, narrow, home-grown comparison is worse at its one job
# than a tool that already lives in this directory. Rebuilt on top of that
# tool instead of copying its logic (two copies of a hashing function drift
# apart and silently disagree - see perf_fingerprint.py's own comment on
# why FIELDS is derived from SAVE_FIELDS rather than hand-maintained here).
#
# Two subprocesses, not one compared against this (the parent) process:
# PYTHONHASHSEED can only be fixed at interpreter start-up, and comparing
# against whatever hash seed the parent test run happened to boot with
# made the old check's sensitivity depend on luck neither run controlled.
# Two explicit, different seeds make it the same every time this suite runs.
#
# 40 years, not perf_fingerprint's own 200-400: detection above was within
# 1-7 years on every scenario, so 40 is nearly 6x the slowest of those - a
# short horizon is not a weaker test here, it is simply not paying for 160+
# extra years of a signal that, per that measurement, is essentially always
# already in by year 7.
_HASH_SEED_HORIZON = 40


def _fingerprint_under_seed(hash_seed, years_cap):
    """Run every perf_fingerprint scenario, capped to `years_cap` years, in a
    fresh subprocess under PYTHONHASHSEED=<hash_seed>. Returns, for each
    scenario, its name and its list of per-year digests - perf_fingerprint's
    own state_of()/digest(), imported and called inside the subprocess
    (that is the only place a hash-seed change can take effect), never
    reimplemented here.
    """
    script = (
        "import json, sys\n"
        "sys.path.insert(0, %r)\n"
        "import perf_fingerprint as F\n"
        "out = []\n"
        "for sc in F.SCENARIOS:\n"
        "    nm = F.name_of(sc)\n"
        "    sc = dict(sc, years=min(sc['years'], %d))\n"
        "    s = F.build(sc)\n"
        "    digs = []\n"
        "    for _ in range(sc['years']):\n"
        "        if getattr(s, 'dead_reason', None):\n"
        "            break\n"
        "        s.step()\n"
        "        digs.append(F.digest(F.state_of(s)))\n"
        "    out.append([nm, digs])\n"
        "print(json.dumps(out))\n"
    ) % (HERE, years_cap)
    det = subprocess.run([sys.executable, "-c", script], capture_output=True,
                         text=True, timeout=600,
                         env=dict(os.environ, PYTHONHASHSEED=str(hash_seed)))
    if det.returncode != 0:
        raise RuntimeError("fingerprint subprocess (hash seed %s) failed: %s"
                           % (hash_seed, det.stderr[-2000:]))
    return json.loads(det.stdout)


def _same_under_other_hash_seed():
    a = _fingerprint_under_seed(0, _HASH_SEED_HORIZON)
    b = _fingerprint_under_seed(1234567, _HASH_SEED_HORIZON)
    if a == b:
        return True, ""
    for (na, da), (nb, db) in zip(a, b):
        if da != db:
            j = next((y for y in range(min(len(da), len(db)))
                      if da[y] != db[y]), min(len(da), len(db)))
            return False, "%s diverged at year %d" % (na, j)
    return False, "run lengths differ: %r vs %r" % (
        [len(d) for _, d in a], [len(d) for _, d in b])


slow_check("...and the same run in a process with a different string hash seed",
           _same_under_other_hash_seed)

# --- BREAK: a permanent deadlock. `logarithms` wants 10,000 scribe-hours a
# year where the society can field 8,750, so the throttle gives back a
# fraction of the work every year - and with no floor under the refund it gave
# back ALL of it. Founder-hours sat at exactly 5.0 for ever, the bill paid,
# the calendar long past, holding the whole scribe pool and freezing eight
# projects behind it - one of them scientific_method, a 230-denarius node
# startable in year 100 and still unbuilt at the horizon.
s_dl = sim(capital=20000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_dl.done.add(_p)
s_dl.scholars = s_dl.artisans = 50.0
s_dl._done_changed()
check("a project needing more of a trade than exists is startable",
      s_dl.start_project("logarithms")[0], s_dl.start_reason("logarithms"))
for _ in range(60):
    s_dl.step()
    if "logarithms" not in s_dl.active:
        break
check("...and it finishes, slowly, instead of freezing for ever",
      "logarithms" in s_dl.done, (s_dl.year, s_dl.active.get("logarithms")))
check("...and it took longer than its calendar floor, because it crawled",
      s_dl.done_year.get("logarithms", 0) - 100 > NODES["logarithms"]["yrs"],
      s_dl.done_year.get("logarithms"))

# --- BREAK: "RUN ENDS: denounced: as a sorcerer" after eleven quiet years,
# with `state` showing "scandal 33.55" and no threshold and no probability -
# on the same screen where eminence explains itself in full.
s_sc = sim(events=True)
s_sc.scandal = 30.0
s_sc.year = 150
s_sc._said_scandal = 0
_st_sc = S._agent_state(s_sc, NODES)
check("state says what scandal is dangerous above",
      _st_sc.get("scandal_danger") is not None, _st_sc.get("scandal_danger"))
check("...and what the chance of being denounced this year is",
      _st_sc.get("chance_of_being_denounced_this_year", 0) > 0,
      _st_sc.get("chance_of_being_denounced_this_year"))
check("...and the page prints both, next to the eminence line that already did",
      "SCANDAL is dangerous above" in _RP("state", _st_sc),
      [l for l in _RP("state", _st_sc).splitlines() if "dangerous above" in l])

# --- BREAK: the advertised price index touched nothing a player feels.
# Revenue ~233 and living costs 230.0 TO THE DECIMAL in all five civs, against
# a selection screen advertising "prices 0.75x to 1.40x Rome" - while project
# costs, wages, the workshop's output and state funding all did scale, so an
# expensive society paid 1.4x to build and ate at Roman prices.
_lc, _rv = {}, {}
for _cid in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
             "england_1300"):
    _s = sim(civ=_cid)
    _lc[_cid] = round(_s.living_cost(), 2)
    _rv[_cid] = round(_s.revenue(), 2)
check("living costs follow this society's price level",
      len(set(_lc.values())) == 5, _lc)
check("...and so does what your practice pays",
      len(set(_rv.values())) == 5, _rv)
check("...and the dearest society really is the dearest",
      max(_lc, key=lambda c: _lc[c]) == "norse_900ad", _lc)
check("...and the cheapest really is the cheapest",
      min(_lc, key=lambda c: _lc[c]) == "han_china_100ad", _lc)


# --- BREAK: "A concern you open reaches its full figure over 3 years" - and a
# concern built in 100 and opened in 130 was at full takings the day its doors
# opened, because the ramp read the year you worked it OUT. Delaying `open`
# was strictly better than opening promptly.
s_rp = sim(capital=500000.0)
_vr = next(k for k in sorted(NODES)
           if s_rp.is_venture(k) and NODES[k]["rev"] > 500 and not NODES[k]["pre"])
s_rp.done.add(_vr); s_rp.done_year[_vr] = 100; s_rp._done_changed()
s_rp.artisans = s_rp.scholars = 20.0
s_rp.year = 130
s_rp.open_venture(_vr)
_ramps = []
for _y in (130, 131, 132, 133):
    s_rp.year = _y
    _ramps.append(round(s_rp.venture_ramp(_vr), 3))
check("a concern opened late still starts small",
      _ramps[0] < 0.4, _ramps)
check("...and reaches its full figure over the years the ledger promises",
      _ramps == [1 / 3.0, 2 / 3.0, 1.0, 1.0][:4]
      or (_ramps[0] < _ramps[1] < _ramps[2] == _ramps[3] == 1.0), _ramps)
# Reopening something you already ran does not restart its custom.
s_rp.year = 140
s_rp.close_venture(_vr)
s_rp.open_venture(_vr)
check("...and reopening a shop the town already knows does not start it over",
      s_rp.venture_ramp(_vr) == 1.0, s_rp.venture_ramp(_vr))

# --- BREAK: "FULL CHAIN BEHIND IT: ... N den" summed the tree's BASE cost and
# applied none of the multipliers the same page prints. The eight
# prerequisites of a telescope came out at 24,175 in all five civilisations.
# Three independent fresh sessions - dispatched together under --jobs.
_chain_cids = ("rome_100ad", "han_china_100ad", "norse_900ad")
_chain_results = _par_map(
    lambda cid: proto([{"cmd": "why", "id": "telescope"}], civ=cid)[0][0].get("chain_cost"),
    _chain_cids)
_chains = dict(zip(_chain_cids, _chain_results))
check("the full-chain bill is quoted at this society's prices",
      len(set(_chains.values())) == 3, _chains)
check("...and the dearest society's chain really is the dearest",
      max(_chains, key=lambda c: _chains[c]) == "norse_900ad", _chains)
# The parts have to add up to the whole, at whatever prices.
_s_ch = sim(civ="norse_900ad")
from engine.data import closure as _closure
# The chain is what is BEHIND it, so the node itself is not in the bill.
_behind = sorted(_closure(NODES, "telescope") - {"telescope"})
check("...and it is the sum of what each of those nodes would actually cost",
      abs(_chains["norse_900ad"]
          - sum(_s_ch.project_cost(x) for x in _behind)) < 0.5,
      (_chains["norse_900ad"],
       round(sum(_s_ch.project_cost(x) for x in _behind), 1)))

# --- BREAK: `risk` applied the 80% chance twice, so "expected lost per
# sacking" was exactly 20% low - a sacking that has happened has happened.
s_rk = sim()
for _k in list(NODES)[:300]:
    s_rk.done.add(_k)
s_rk._done_changed()
_krk = s_rk.knowledge_risk()
check("what a sacking costs is not discounted by the chance it happens",
      abs(_krk["expected_technologies_lost_per_sacking"]
          - _krk["technologies_at_risk"] * _krk["fraction_lost_when_it_happens"]) < 0.6,
      _krk["expected_technologies_lost_per_sacking"])
check("...and the chance it costs you anything is reported separately",
      _krk.get("and_the_chance_a_sacking_costs_you_anything") is not None,
      _krk.get("and_the_chance_a_sacking_costs_you_anything"))

# --- BREAK: "CLOSE TO THE LIMIT ... (103%) ... every project in hand is
# halted" in a year when nothing was halted, because it had already happened.
s_pl = sim()
s_pl.capital = -s_pl.credit_limit() * 1.03
s_pl.warn_near_the_limit(105)
check("the limit warning is about what is ahead of you, not behind",
      not s_pl.log, [m for _, m in s_pl.log])

# --- BREAK: `bribe 1` refused at 0% protection as "already as protected as
# money can make you".
_rb, _, _ = proto([{"cmd": "bribe", "amount": 1}])
check("a bribe too small to matter says so, not that you are already covered",
      "too little" in (_rb[0].get("error") or ""), _rb[0].get("error"))


# --- BREAK: "FULL CHAIN BEHIND IT" printed identical figures in year 436
# after 227 technologies as in year 100 with nothing built.
s_cn = sim()
_r_before = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
for _p in ("patron_local", "workshop_first", "identity_cover"):
    s_cn.done.add(_p)
s_cn._done_changed()
_r_after = S._agent_dispatch(s_cn, NODES, {"cmd": "why", "id": "telescope"})
check("the chain behind a node counts down as you build it",
      _r_after["chain_size"] < _r_before["chain_size"],
      (_r_before["chain_size"], _r_after["chain_size"]))
check("...in hours as well as in nodes",
      _r_after["chain_founder_hours"] < _r_before["chain_founder_hours"],
      (_r_before["chain_founder_hours"], _r_after["chain_founder_hours"]))
check("...and in money",
      _r_after["chain_cost"] < _r_before["chain_cost"],
      (_r_before["chain_cost"], _r_after["chain_cost"]))
check("...and it still says how long the whole road was",
      _r_after["chain_size_counting_what_you_have_built"]
      == _r_before["chain_size_counting_what_you_have_built"],
      _r_after["chain_size_counting_what_you_have_built"])

# --- BREAK: the household-room refusal handed back the advice for BUYING
# people, every word of which needs room you do not have. A play tester with a
# ceiling of 166.9 against a node wanting 200 craftsmen wrote that none of the
# three remedies the message suggests works.
s_rm = sim(capital=1000000.0)
_ok_rm, _why_rm = s_rm.hire("smith", 20)
check("a room refusal names what raises the room, not what buys people",
      not _ok_rm and "built" in _why_rm and "hire" not in _why_rm.split(".")[1],
      _why_rm)
check("...and names the nearest of them first, not the largest",
      _why_rm.index("workshop_first") < _why_rm.index("school_founded"),
      _why_rm[_why_rm.index("built"):][:120])
s_rm2 = sim(capital=1000000.0)
s_rm2.done.update(NODES); s_rm2._done_changed()
# OPEN, not just built: a ROOM_SOURCES entry that is done but not operating
# is exactly the case the next block tests (reopen advice, not "you have
# everything"), so "every one of them" has to mean everything built AND
# running, the same distinction run_it exists to set up everywhere else.
s_rm2.operating.update(k for k, _ in s_rm2.ROOM_SOURCES if k in NODES)
check("...and says so plainly when you already hold every one of them",
      "every one of them" in s_rm2._room_advice(), s_rm2._room_advice())

# --- BREAK: a ROOM_SOURCES institution built and then SHUT (attrition, a
# bad year, or the player's own `mothball`) vanished from this advice
# entirely - filtered out for being `in self.done`, exactly like something
# never built, even though staff_capacity() had already stopped counting
# its places the moment it closed. The advice recommended building a new,
# dearer institution instead of reopening the one already paid for.
s_rm3 = sim(capital=1000000.0)
run_it(s_rm3, "workshop_first", "school_founded")
_advice_open = s_rm3._room_advice()
s_rm3.operating.discard("school_founded")
_advice_shut = s_rm3._room_advice()
check("a shut room-source is offered back as the cheap fix, not silently "
      "dropped from the advice",
      "school_founded" in _advice_shut and "reopen" in _advice_shut.lower(),
      _advice_shut)
check("...and it is not also still claimed as an open place in the same "
      "breath",
      "school_founded" not in _advice_open or "reopen" not in _advice_open.lower(),
      (_advice_open, _advice_shut))

# --- and the same fix, for the scholar/artisan hiring-pool advice
# (_staff_advice / STAFF_SOURCES), which has its own, separate list.
s_sa = sim(capital=1000000.0)
run_it(s_sa, "school_founded")
s_sa.operating.discard("school_founded")
_staff_shut = s_sa._staff_advice("scholars")
check("the scholar-pool advice offers to reopen a shut school rather than "
      "silently treating it as already covered",
      "school_founded" in _staff_shut and "reopen" in _staff_shut.lower(),
      _staff_shut)

# --- BREAK: ROOM_SOURCES carried a stale id, "bessemer_openhearth", which
# does not exist in the tree (the real id is met_open_hearth_furnace) -
# STAFF_CAPACITY_SOURCES was corrected to the real id and this second,
# separate table was not, so the 65 places an open-hearth furnace is worth
# were never once offered as advice even though the arithmetic (via
# staff_capacity) already counted them correctly.
check("ROOM_SOURCES names real node ids only - no stale reference silently "
      "filtered out of every reply that reads this table",
      all(k in NODES for k, _ in s_rm3.ROOM_SOURCES),
      [k for k, _ in s_rm3.ROOM_SOURCES if k not in NODES])


# --- BREAK: three places said the town could field 8,750 scribe-hours a year,
# and commissioning the full 8,750 ON TOP of the standing pool let a
# 10,000-hour project finish. Real ceiling 17,500; every one of the three
# statements false.
# TWO CHANNELS, each bounded and each named. Hiring draws on the people who
# live here; a commission is a job placed with an outside shop, which
# subcontracts - dearer per hour, and bounded in turn by what the local trade
# can spare. Stated as ONE ceiling of 8,750 it was false (the real one was
# 17,500); collapsed into one it made commissioning buy byte-identical
# progress and be pointless. Both statements have to be on the screen.
s_cm = sim(capital=5000000.0)
_ceiling = s_cm.market_supply("scribe")
s_cm.commission("scribe", _ceiling * 0.9)
check("commissioning does not raise how many of a trade LIVE here",
      abs(s_cm.market_supply_split("scribe")[0]
          - sim(capital=5000000.0).market_supply_split("scribe")[0]) < 1e-6,
      s_cm.market_supply_split("scribe")[0])
check("...and it does add hours you can actually call on",
      s_cm.hours_you_can_call_on("scribe") > _ceiling, 
      (_ceiling, s_cm.hours_you_can_call_on("scribe")))
check("...and you cannot commission past what the trade here can spare",
      s_cm.commission("scribe", _ceiling)[0] is False,
      s_cm.commission("scribe", _ceiling)[1])
_rc2, _, _ = proto([{"cmd": "labour", "trade": "scribe"}])
check("...and `labour` names both channels, not one ceiling",
      _rc2[0]["trade"].get("hours_you_could_still_commission") is not None
      and _rc2[0]["trade"].get("hours_available_to_you_in_all")
      >= _rc2[0]["trade"].get("hours_the_market_can_supply"),
      _rc2[0]["trade"])

# --- BREAK: a senatorial patron added 15,000 to the credit line whoever you
# were, so a household with 1,800 of revenue could owe 23,000 - about 1,500 a
# year of interest against 1,800 of income, which no practice can ever repay.
s_cl = sim()
_thin = s_cl.credit_limit()
s_cl.done.add("patron_senatorial"); s_cl._done_changed()
check("a grand friend does not lend you more than your income can carry",
      s_cl.credit_limit() < _thin * 3, (_thin, s_cl.credit_limit()))
check("...and the interest on the whole line stays under what you earn",
      s_cl.credit_limit() * s_cl.debt_interest_rate() < s_cl.revenue(),
      (s_cl.credit_limit() * s_cl.debt_interest_rate(), s_cl.revenue()))
check("...while a founder with a practice can still just reach a cover identity",
      sim().capital + sim().credit_limit() >= sim().project_cost("identity_cover"),
      (sim().capital + sim().credit_limit(), sim().project_cost("identity_cover")))

# --- BREAK: status upkeep was unconditional - 1,100 a year for a citizenship
# and a senatorial patron a ruined household could not afford and had no way
# to shed - and it bled a Rome run 741 a year for sixty-four years.
s_st = sim()
s_st.done.update({"citizenship", "patron_senatorial"}); s_st._done_changed()
_rich = sim(capital=2000000.0)
_rich.done.update({"citizenship", "patron_senatorial"}); _rich._done_changed()
# The two ranks are worth 1,100 a year of show at Rome's prices; a household
# with 233 of income does not pay it.
check("a ruined household stops keeping up appearances",
      s_st.living_cost() < sim().living_cost() + 50.0,
      (s_st.living_cost(), sim().living_cost()))
check("...and a household that can afford the show still pays for it",
      _rich.living_cost() > s_st.living_cost() * 2, (_rich.living_cost(),
                                                     s_st.living_cost()))

# --- BREAK: the optimizer's budget for new work counted upkeep, living costs
# and mines and NOT the interest it was already paying, so a household bleeding
# 552 a year decided it had five years of headroom against money that did not
# exist.
s_bd = sim(capital=-20000.0, manual=False)
s_bd.insolvent_years = 20
_before = len(s_bd.active)
s_bd.step()
check("a household deep in arrears does not commit to new work",
      len(s_bd.active) <= _before + 1, (len(s_bd.active), _before))


# --- BREAK: "There's no 'why am I stuck?' view - three separate 90-250-year
# stalls, each caused by one node blocked on one thing, each found by typing
# `why` at a guess." Every tester of rounds eight and nine said some version.
_rs, _, _ = proto([{"cmd": "stuck"}])
check("there is one command that answers why you are not getting on",
      _rs and _rs[0].get("ok") and "what_is_holding_you_up" in _rs[0],
      list(_rs[0])[:5] if _rs else None)
# THIS CHECK USED TO ASSERT THE BUG. It required turn one to report nothing
# holding you up - and turn one is precisely when nothing is running, which a
# later play tester typed `stuck` to find out and was told "nothing: you have
# work in hand, money to pay for it and people to do it". It was the first
# thing they typed and it was false.
check("...and on turn one it says you have started nothing",
      any(r.get("what") == "you have started nothing"
          for r in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
check("...and names something you could start instead",
      any("start " in str(r.get("why")) for r in _rs[0]["what_is_holding_you_up"]),
      _rs[0]["what_is_holding_you_up"])
# ...and once something IS running and nothing is wrong, it says so plainly
# without claiming work in hand that is not there.
_s_ok = sim(capital=500000.0)
_s_ok.start_project("identity_cover")
_rs_ok = S._agent_dispatch(_s_ok, NODES, {"cmd": "stuck"})
check("...and with work in hand and money it says nothing is holding you up",
      isinstance(_rs_ok.get("what_is_holding_you_up"), str)
      or all(r.get("what") != "you have started nothing"
             for r in _rs_ok["what_is_holding_you_up"]),
      _rs_ok.get("what_is_holding_you_up"))
check("...and names the cheapest thing you could actually begin",
      _rs[0].get("and_the_cheapest_thing_you_could_start_now") in NODES,
      _rs[0].get("and_the_cheapest_thing_you_could_start_now"))
_rs2, _, _ = proto([{"cmd": "start", "id": "identity_cover"},
                    {"cmd": "step", "years": 3},
                    {"cmd": "stuck"}])
_held = _rs2[-1]["what_is_holding_you_up"]
check("...and once you are committed and in the red it names both",
      not isinstance(_held, str)
      and {"work in hand", "arrears"} <= {r["what"] for r in _held},
      [r.get("what") for r in _held] if not isinstance(_held, str) else _held)
check("...and says what each piece of work in hand is waiting for",
      any(r.get("each_waiting_on") for r in _held if isinstance(r, dict)), _held)
check("...and it renders as a page, not a dict dump",
      "WHY YOU ARE NOT GETTING ON" in _RP("stuck", _rs2[-1])
      and "{" not in _RP("stuck", _rs2[-1]), _RP("stuck", _rs2[-1])[:70])
_rst, _, _ = proto([{"cmd": "state"}])
check("...and `state` advertises it every turn",
      any("stuck" in x for x in (_rst[0].get("also_available") or [])),
      _rst[0].get("also_available"))

# --- BREAK: "things you built and never opened" picked the best-margin shut
# concern by revenue minus upkeep alone and told the player to 'open' it,
# without ever checking whether open_venture would actually agree - measured
# directly against the dice-free Rome credit/named-trade trap (PATH_SEARCH.md):
# at year 700, free_art sits at 0.00 and `stuck` was recommending 'open
# lens_grinding', which needs 2.13 craftsmen to supervise and refuses outright.
# lens_grinding needs more craftsmen to supervise (2.13) than a fresh
# household has free even before anything else competes for them (founder
# alone is worth 1.0), so this is reproducible with nothing but a closed
# prerequisite chain, no multi-century run required.
s_shut = sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_shut.done.add(_p)
s_shut.done.add("lens_grinding")
s_shut._done_changed()
check("lens_grinding is done, not operating, and genuinely profitable - the "
      "exact shape 'stuck' looks for",
      s_shut.is_venture("lens_grinding")
      and "lens_grinding" not in s_shut.operating
      and NODES["lens_grinding"]["rev"] > NODES["lens_grinding"]["up"],
      (s_shut.is_venture("lens_grinding"), "lens_grinding" in s_shut.operating))
_sch_free_sg, _art_free_sg = s_shut.venture_staff_free()
_need_sch_sg, _need_art_sg = s_shut.venture_hands("lens_grinding")
check("...and a fresh household genuinely cannot supervise it yet",
      _need_art_sg > _art_free_sg + 0.01,
      (_need_art_sg, _art_free_sg))
_stuck_shut = S._agent_dispatch(s_shut, NODES, {"cmd": "stuck"})
_shut_reason = next((r for r in _stuck_shut["what_is_holding_you_up"]
                    if isinstance(r, dict)
                    and r.get("what", "").startswith("things you built")),
                   None)
check("`stuck` never tells a player to 'open' something open_venture will "
      "actually refuse",
      _shut_reason is not None
      and "'open lens_grinding'" not in _shut_reason.get("why", ""),
      _shut_reason)
check("...and instead says the true reason (craftsmen, here) it cannot be "
      "opened, so a player knows what to fix rather than spending a turn on "
      "a refusal",
      _shut_reason is not None and "craftsmen to supervise" in _shut_reason.get("why", ""),
      _shut_reason.get("why") if _shut_reason else None)

# ...and the old, simpler advice still fires once the household genuinely CAN
# open the thing - the fix narrows the claim, it does not silence it.
s_can = sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_can.done.add(_p)
s_can.done.add("lens_grinding")
s_can._done_changed()
s_can.artisans = 10.0
_stuck_can = S._agent_dispatch(s_can, NODES, {"cmd": "stuck"})
_can_reason = next((r for r in _stuck_can["what_is_holding_you_up"]
                   if isinstance(r, dict)
                   and r.get("what") == "things you built and never opened"),
                  None)
check("...and once there really are enough hands free, `stuck` goes back to "
      "naming the concrete 'open X' command",
      _can_reason is not None and "'open lens_grinding'" in _can_reason.get("why", ""),
      _can_reason)


# --- BREAK: a trade you taught counts as existing for ever, so once the last
# machinist had died of old age auto_train skipped every node that needed one
# and nobody was ever taught again. A Rome run built 829 technologies, sat on
# 31.9M denarii, and could not begin precision_three_plate - which gates
# master_screw, the screw lathe and ninety-nine of the hundred and forty-six
# nodes on the road to the goal.
s_rt = sim(capital=2000000.0, manual=False)
s_rt.trades_created.add("machinist")          # taught once, long ago
s_rt.employees.pop("machinist", None)
s_rt._resync_pools()
check("a trade taught and then lost counts as gone, not as available",
      s_rt.trade_available("machinist")
      and s_rt.market_supply("machinist") <= 0.0,
      (s_rt.trade_available("machinist"), s_rt.market_supply("machinist")))
for _ in range(6):
    s_rt.step()
check("...and the engine teaches it again rather than skipping every node "
      "that needs it",
      s_rt.market_supply("machinist") > 0
      or s_rt._trade_headcount_pending("machinist") > 0,
      (s_rt.market_supply("machinist"),
       s_rt._trade_headcount_pending("machinist")))
# But not every year: teaching two costs about 900 of a 2,000-hour year.
# FOUR SECONDS: forty years of an optimizer run to watch a cooldown that only
# has meaning across decades. Per TRADE: teaching four different trades over
# forty years is fine; teaching the same one four times is the treadmill that
# cost three Rome seeds most of what they built.
def _reteaching_is_once_a_generation():
    s_ = sim(capital=2000000.0, manual=False)
    s_.trades_created.add("machinist")
    per_trade = {}
    for _ in range(40):
        before = dict(getattr(s_, "last_taught", {}))
        s_.step()
        for t, y in getattr(s_, "last_taught", {}).items():
            if before.get(t) != y:
                per_trade[t] = per_trade.get(t, 0) + 1
    return (all(v <= 40 // s_.RETEACH_EVERY + 1 for v in per_trade.values()),
            per_trade)

slow_check("...and no more than once a generation FOR THE SAME TRADE",
           _reteaching_is_once_a_generation)


# --- BREAK: `train machinist 4` quietly ate 1,800 of a play tester's 2,000
# founder-hours and, with nothing left to supervise with, closed a dozen
# concerns as a side effect. The reply was six words about two years' time.
_rt3, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 4}], kit="absurd")
check("teaching says what it took out of your year",
      "of your own hours" in json.dumps(_rt3[0])
      and "left this year" in json.dumps(_rt3[0]), _rt3[0])
check("...and what it cost to keep them while they learn",
      "denarii" in json.dumps(_rt3[0]), _rt3[0])


# --- BREAK: household_room exists because `hire` and `buy` used different
# numbers. `train` was the third verb and checked nothing at all, so the
# optimizer taught its way to a headcount of 26.9 against room for 6 - minus
# eighteen places - and then could not hire the artisans to supervise
# anything.
s_tr3 = sim(capital=2000000.0)
# Widen the literacy ceiling first, so the ROOM is what binds rather than the
# pool of people who can read - the tightest constraint should be the one that
# speaks, and here we are testing the other one.
for _k in ("rag_paper", "printing_press", "if_movable_type", "academy_network"):
    if _k in NODES:
        s_tr3.apply_tech_effects(_k)
_room0 = s_tr3.household_room()
check("a fresh household has room for a few people and no more",
      0 < _room0 < 20, _room0)
check("...and the literacy ceiling is not what binds here",
      s_tr3.literate_capacity("machinist") > _room0 + 1,
      (s_tr3.literate_capacity("machinist"), _room0))
# Fill the household first, which is the state the tester was in: the hours
# check bites long before the room does at any larger number, because teaching
# costs 450 founder-hours a head.
s_tr3.hire("smith", int(_room0))
_ok_t3, _why_t3 = s_tr3.train("machinist", 1)
check("teaching past what you can feed and house is refused",
      not _ok_t3 and "feed, house and oversee" in _why_t3, _why_t3)
check("...and it says there is no room for even one",
      "no room for even one" in _why_t3, _why_t3)
check("...and what makes room, which is not what buys people",
      "built" in _why_t3, _why_t3)
s_tr4 = sim(capital=2000000.0)
check("...and teaching within the room still works",
      s_tr4.train("machinist", 1)[0], s_tr4.train("machinist", 1)[1])
# The three verbs must agree, which is the whole reason household_room exists.
s_ag = sim(capital=2000000.0)
_r = s_ag.household_room()
s_ag.hire("smith", int(_r))          # fill it exactly
check("hire, buy and train are all bounded by the same one number",
      s_ag.hire("smith", 1)[0] is False
      and s_ag.train("machinist", 1)[0] is False
      and s_ag.buy_slaves(1) <= 0,
      (_r, s_ag.household_room()))


# --- BREAK: "this society's literacy will not supply more than 6.4 scholars
# in total, ever" gates the GOAL, which wants twenty-five, and appeared in no
# screen at all: a play tester found it in a refusal message in year 463 of a
# 500-year game. The single thing that decided whether their run could be won.
_rl3, _, _ = proto([{"cmd": "labour", "trade": "scholar"},
                    {"cmd": "labour", "trade": "smith"},
                    {"cmd": "why", "id": GOAL}])
check("a lettered trade shows the ceiling on how many can ever exist here",
      _rl3[0]["trade"].get("most_this_society_can_ever_supply") is not None,
      _rl3[0]["trade"].get("most_this_society_can_ever_supply"))
check("...and says what widens it",
      "printing" in str(_rl3[0]["trade"].get("what_widens_it")),
      _rl3[0]["trade"].get("what_widens_it"))
check("...and a trade needing no letters carries no such ceiling",
      _rl3[1]["trade"].get("most_this_society_can_ever_supply") is None,
      _rl3[1]["trade"].get("most_this_society_can_ever_supply"))
check("and `why` warns when a node wants more scholars than can ever exist",
      _rl3[2].get("more_scholars_than_this_society_can_supply"),
      _rl3[2].get("more_scholars_than_this_society_can_supply"))
check("...and more craftsmen than the household could ever hold",
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"),
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"))
_rl4, _, _ = proto([{"cmd": "why", "id": "horse_collar"}])
check("...and says nothing of the kind about a node you could staff",
      not _rl4[0].get("more_scholars_than_this_society_can_supply"),
      _rl4[0].get("more_scholars_than_this_society_can_supply"))


