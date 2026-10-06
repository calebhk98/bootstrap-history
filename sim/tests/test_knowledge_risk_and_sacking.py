"""What a sacking actually costs, and whether `risk` told the truth
about it beforehand: the corpus hedge (corpus_written vs corpus_dispersed),
the KNOWLEDGE LOST announcement, and the sack's effect on the whole
household's headcount.
"""
from .harness import *  # noqa: F401,F403


class _AlwaysSackRNG:
    """random() always fires the sack; sample() takes the front of the list,
    so how many are lost depends only on the fraction, never on luck."""
    def random(self):
        return 0.0
    def sample(self, population, count):
        return list(population)[:count]


def _force_sack(household, name="TEST SACK"):
    household.rng = _AlwaysSackRNG()
    household.civ = dict(household.civ)
    household.civ["hazards"] = [{"name": name, "years": [household.year, household.year],
                                 "sack_chance": 1.0}]


# One game serves the hedge, risk-arithmetic and headcount checks.
household_main = sim(capital=500000.0)

# --- `risk` offered a hedge with no word of why. Every entry must say what it leads to.
_steps = []
for _kind in sorted(household_main.HAZARD_COUNTERS):
    _steps += household_main.hedge_first_steps(_kind)
check("every hedge the game suggests says what it gets you",
      _steps and all(step.get("because_it_gives_you") for step in _steps),
      [step["id"] for step in _steps if not step.get("because_it_gives_you")][:3])
check("...and a prerequisite says which counter it is a step toward",
      any(str(step["because_it_gives_you"]).startswith("a step toward")
          for step in _steps))

# --- The hedge follows what you KNOW, not what you run.
_risk_before = household_main.knowledge_risk()
household_main.done.add("corpus_written"); household_main._done_changed()
_hedge_known = household_main.knowledge_risk()["hedged_by"]
household_main.open_venture("corpus_written")
_hedge_open = household_main.knowledge_risk()["hedged_by"]
check("building the corpus hedges you; opening it changes nothing",
      _risk_before["hedged_by"] is None and _hedge_known == "corpus_written"
      and _hedge_open == _hedge_known, (_risk_before["hedged_by"], _hedge_known, _hedge_open))
check("no corpus built: `risk` declares the undefended chance and fraction",
      _risk_before["loss_chance_if_a_site_is_sacked"] == 0.80
      and _risk_before["fraction_lost_when_it_happens"] == 0.40, _risk_before)

# --- `risk` applied the chance of a sacking twice, so the expected loss was low.
for _node_id in list(NODES)[:300]:
    household_main.done.add(_node_id)
household_main._done_changed()
_risk_many = household_main.knowledge_risk()
check("what a sacking costs is not discounted by the chance it happens",
      abs(_risk_many["expected_technologies_lost_per_sacking"]
          - _risk_many["technologies_at_risk"] * _risk_many["fraction_lost_when_it_happens"]) < 0.6,
      _risk_many["expected_technologies_lost_per_sacking"])
check("...and the chance it costs you anything is reported separately",
      _risk_many.get("and_the_chance_a_sacking_costs_you_anything") is not None,
      _risk_many.get("and_the_chance_a_sacking_costs_you_anything"))

# --- A sack hit artisans and scholars but left hired staff untouched, so the
# announced loss and the real headcount fall disagreed.
household_main.artisans, household_main.scholars, household_main.directors_extra = 20.0, 10.0, 5.0
household_main.employees = {"smith": 40.0, "scribe": 30.0, "mason": 20.0}
_people_before = household_main.artisans + household_main.scholars + sum(household_main.employees.values())
_staff_before = sum(household_main.employees.values())
_force_sack(household_main)
_log_start = len(household_main.log)
household_main._shocks(household_main.year)
_sack_messages = [message for _, message in household_main.log[_log_start:] if "a site is sacked" in message]
_announced = float(re.search(r"([\d.]+) of your people gone", _sack_messages[0]).group(1)) if _sack_messages else 0.0
_people_after = household_main.artisans + household_main.scholars + sum(household_main.employees.values())
check("a sack's own report of how many people are gone and the actual fall "
      "in total headcount (artisans + scholars + every hired trade) are the same number",
      _announced > 0 and abs((_people_before - _people_after) - _announced) < 0.05,
      (_announced, _people_before - _people_after))
check("...and hired staff are among those lost, not only the generic pools",
      sum(household_main.employees.values()) < _staff_before,
      (sum(household_main.employees.values()), _staff_before))
_state_total = S._agent_dispatch(household_main, NODES, {"cmd": "state"})["employees_total"]
check("...and `state`'s employees_total reflects that same fall",
      abs(_state_total - sum(household_main.employees.values())) < 1e-6, _state_total)

# --- A sacking destroyed technologies and named none of them.
household_sack = sim(events=True, capital=500000.0)
for _node_id in list(NODES)[:400]:
    household_sack.done.add(_node_id)
household_sack.done.add("corpus_dispersed")
household_sack._done_changed()
household_sack.rng = random.Random(11)
for _year in range(150, 320):
    household_sack.year = _year
    household_sack._shocks(_year)
    if getattr(household_sack, "forgotten", None):
        break
check("a sacking names the technologies it destroyed",
      any("KNOWLEDGE LOST" in message and "_" in message.split("forgotten")[-1]
          for _, message in household_sack.log),
      [message for _, message in household_sack.log if "KNOWLEDGE LOST" in message][:1])
_risk_after = household_sack.knowledge_risk()
check("...and `risk` lists what you have to build again",
      _risk_after.get("you_have_already_lost", 0) > 0
      and _risk_after.get("and_have_to_build_again"),
      _risk_after.get("you_have_already_lost"))
check("...and everything it lists really is gone from what you know",
      all(node_id not in household_sack.done for node_id in _risk_after["and_have_to_build_again"]),
      [node_id for node_id in _risk_after["and_have_to_build_again"] if node_id in household_sack.done])
check("corpus_dispersed is not among what a sack over real random draws forgets",
      "corpus_dispersed" not in (getattr(household_sack, "forgotten", None) or {}),
      getattr(household_sack, "forgotten", None))


# --- `risk` and the sack must agree about what a closed corpus is worth: both
# answer from Sim.corpus_hedge(), a built corpus counts whether or not it runs.
def _corpus_sack_scenario(hedge_node, node_count=300):
    household = sim(capital=1_000_000.0)
    candidates = sorted(node_id for node_id in NODES if node_id not in household.granted)[:node_count]
    household.done.update(candidates)
    household.done.add(hedge_node)
    household._done_changed()
    _force_sack(household)
    return household


def _expected_losable(sim_state):
    return sorted(node_id for node_id in sim_state.done
                  if node_id not in sim_state.granted and node_id != "corpus_dispersed")


household_written = _corpus_sack_scenario("corpus_written")
_risk_written = household_written.knowledge_risk()
check("corpus_written, closed (not running): `risk` still credits it",
      _risk_written["hedged_by"] == "corpus_written"
      and _risk_written["fraction_lost_when_it_happens"] == 0.22, _risk_written)
_losable_written = _expected_losable(household_written)
household_written._shocks(household_written.year)
_lost_written = len(getattr(household_written, "forgotten", None) or {})
check("...and the sack takes exactly the fraction `risk` told you to expect",
      _lost_written == max(1, int(len(_losable_written) * 0.22)), (_lost_written, len(_losable_written)))

household_dispersed = _corpus_sack_scenario("corpus_dispersed")
_risk_dispersed = household_dispersed.knowledge_risk()
check("corpus_dispersed, closed (not running): `risk` credits its hedge",
      _risk_dispersed["hedged_by"] == "corpus_dispersed"
      and _risk_dispersed["fraction_lost_when_it_happens"] == 0.08, _risk_dispersed)
_losable_dispersed = _expected_losable(household_dispersed)
_log_start = len(household_dispersed.log)
household_dispersed._shocks(household_dispersed.year)
_forgotten_dispersed = getattr(household_dispersed, "forgotten", None) or {}
_lost_dispersed = len(_forgotten_dispersed)
check("FAILS IF `risk` AND THE SACK EVER DISAGREE: a closed corpus_dispersed makes "
      "the sack take the fraction `risk` declared, not corpus_written's",
      _lost_dispersed == max(1, int(len(_losable_dispersed) * 0.08)), (_lost_dispersed, len(_losable_dispersed)))
check("...less damage than a closed corpus_written sack took",
      _lost_dispersed < _lost_written, (_lost_dispersed, _lost_written))

# Dispersed copies sit beyond one site's reach; ordinary nodes beside it are not spared.
check("corpus_dispersed is never among what the sack forgets, while ordinary nodes beside it go",
      "corpus_dispersed" not in _forgotten_dispersed and _lost_dispersed > 0, _forgotten_dispersed)

# The KNOWLEDGE LOST text is built from how things stood before the loss.
_lost_messages = [message for _, message in household_dispersed.log[_log_start:] if "KNOWLEDGE LOST" in message]
check("a sack that cannot touch corpus_dispersed never claims the corpus was "
      "never dispersed, nor that the corpus itself went",
      bool(_lost_messages)
      and "never printed and dispersed" not in _lost_messages[0]
      and "CORPUS ITSELF WENT" not in _lost_messages[0], _lost_messages)

# --- A sack says what it did to the road to the goal.
household_goal = sim(capital=1_000_000.0)
_on_road = [node_id for node_id in sorted(S.closure(NODES, GOAL))
            if node_id not in household_goal.granted][:6]
check("a non-starting node on the actual road to the goal exists to test against",
      len(_on_road) >= 1, _on_road)
household_goal.done.update(_on_road)
household_goal._done_changed()
_force_sack(household_goal, "TEST CRISIS")
_log_start = len(household_goal.log)
household_goal._shocks(household_goal.year)
_goal_messages = [message for _, message in household_goal.log[_log_start:] if "KNOWLEDGE LOST" in message]
check("the KNOWLEDGE LOST event names how many forgotten technologies stood on the road to the goal",
      bool(_goal_messages) and "road to your goal" in _goal_messages[0], _goal_messages)
check("...and points at 'path' as where to see the route's new shape",
      bool(_goal_messages) and "'path'" in _goal_messages[0], _goal_messages)
