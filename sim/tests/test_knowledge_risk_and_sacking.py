"""What a sacking actually costs, and whether `risk` told the truth
about it beforehand: the corpus hedge (corpus_written vs corpus_dispersed),
the KNOWLEDGE LOST announcement, and the sack's effect on the whole
household's headcount.

Regrouped from test_round8_fixes.py and test_round9.py - see CLAUDE.md's
test-file reorganisation note. Checks moved verbatim; each one's own comment
explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: `risk` offered `horse_collar` as a hedge against the Antonine
# plague with no word of why. Every entry must say what it leads to.
s_hz = sim()
_steps = []
for _kind in sorted(S.Sim.HAZARD_COUNTERS):
    _steps += s_hz.hedge_first_steps(_kind)
check("every hedge the game suggests says what it gets you",
      _steps and all(step.get("because_it_gives_you") for step in _steps),
      [step["id"] for step in _steps if not step.get("because_it_gives_you")][:3])
check("...and a prerequisite says which counter it is a step toward",
      any(str(step["because_it_gives_you"]).startswith("a step toward")
          for step in _steps))

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
      any("KNOWLEDGE LOST" in message and "_" in message.split("forgotten")[-1]
          for _, message in s_sack.log),
      [message for _, message in s_sack.log if "KNOWLEDGE LOST" in message][:1])
_kr = s_sack.knowledge_risk()
check("...and `risk` lists what you have to build again",
      _kr.get("you_have_already_lost", 0) > 0
      and _kr.get("and_have_to_build_again"),
      _kr.get("you_have_already_lost"))
check("...and everything it lists really is gone from what you know",
      all(node_id not in s_sack.done for node_id in _kr["and_have_to_build_again"]),
      [node_id for node_id in _kr["and_have_to_build_again"] if node_id in s_sack.done])
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
    def sample(self, population, count):
        return list(population)[:count]
s_shg.rng = _ShgZeroRNG()
s_shg.civ = dict(s_shg.civ)
s_shg.civ["hazards"] = [{"name": "TEST SACK", "years": [s_shg.year, s_shg.year],
                         "sack_chance": 1.0}]
_before_shg = len(s_shg.log)
s_shg._shocks(s_shg.year)
_shg_msgs = [message for _, message in s_shg.log[_before_shg:] if "a site is sacked" in message]
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
    def sample(self, population, count):
        return list(population)[:count]


def _corpus_sack_scenario(hedge_node, n_done=300):
    household = sim(capital=1_000_000.0)
    cands = sorted(node_id for node_id in NODES if node_id not in household.granted)[:n_done]
    household.done.update(cands)
    if hedge_node:
        household.done.add(hedge_node)
    household._done_changed()
    household.rng = _AlwaysSackRNG()
    household.civ = dict(household.civ)
    household.civ["hazards"] = [{"name": "TEST SACK", "years": [household.year, household.year],
                         "sack_chance": 1.0}]
    return household


def _expected_losable(sim_state):
    return sorted(node_id for node_id in sim_state.done
                  if node_id not in sim_state.granted
                  and node_id != "corpus_dispersed")


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
# already outside the sack's non-starting reach on its own, with or without this
# fix - one set of books in one place was never the node this mechanism
# could take either way; only corpus_dispersed's own tier made it eligible
# before this fix, and only this fix's exclusion takes it out again). A
# second, ordinary non-starting node sitting right next to corpus_dispersed in
# `done` is NOT spared.
s_f3w = sim(capital=500000.0)
_f3_other = next(node_id for node_id in NODES if node_id != "corpus_dispersed" and node_id not in s_f3w.granted)
s_f3w.done.update(["corpus_dispersed", _f3_other])
s_f3w._done_changed()
s_f3w.rng = _AlwaysSackRNG()
s_f3w.civ = dict(s_f3w.civ)
s_f3w.civ["hazards"] = [{"name": "TEST SACK", "years": [s_f3w.year, s_f3w.year],
                         "sack_chance": 1.0}]
s_f3w._shocks(s_f3w.year)
check("an ordinary non-starting node sharing the sack with corpus_dispersed is "
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
for _k in sorted(node_id for node_id in NODES if node_id not in s_f2.granted and node_id != "corpus_dispersed")[:200]:
    s_f2.done.add(_k)
s_f2._done_changed()
s_f2.rng = _AlwaysSackRNG()
s_f2.civ = dict(s_f2.civ)
s_f2.civ["hazards"] = [{"name": "TEST SACK", "years": [s_f2.year, s_f2.year],
                        "sack_chance": 1.0}]
_before_f2 = len(s_f2.log)
s_f2._shocks(s_f2.year)
_f2_msgs = [message for _, message in s_f2.log[_before_f2:] if "KNOWLEDGE LOST" in message]
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
# playtest/fixtures/rome_380_corpus_bug.json is the fixture a player
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
_FIXTURE_380 = os.path.join(ROOT, "playtest", "fixtures",
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
_fix_losable_before = [node_id for node_id in s_fix.done
                       if node_id not in s_fix.granted]
check("...and its losable pool (done, non-starting, not granted) really is "
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
_fix_msgs = [message for _, message in s_fix.log[_before_fix_log:] if "KNOWLEDGE LOST" in message]
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
    def sample(self, population, count):
        return list(population)[:count]
s_kr2 = sim(capital=1_000_000.0)
_gc2 = sorted(S.closure(NODES, GOAL))
_on_road_cands = [node_id for node_id in _gc2 if node_id not in S.Sim(NODES, PRICES, WAGES, GOODS).granted][:6]
check("a non-starting node on the actual road to the goal exists to test "
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
_kr2_msgs = [message for _, message in s_kr2.log[_before_kr2:] if "KNOWLEDGE LOST" in message]
check("the KNOWLEDGE LOST event names how many of the forgotten "
      "technologies stood on the road to the current goal, in the same "
      "breath as the loss itself",
      bool(_kr2_msgs) and "road to your goal" in _kr2_msgs[0],
      _kr2_msgs)
check("...and points at 'path' as where to see the route's new shape, "
      "rather than leaving that to be discovered by comparison",
      bool(_kr2_msgs) and "'path'" in _kr2_msgs[0], _kr2_msgs)

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
