"""Scenarios (Complaint 640; the rules are in test_knowledge_risk_and_sacking): what a sacking costs on a whole game,
and whether `risk` told the truth about it beforehand."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of


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

# --- The hedge follows what you KNOW, not what you run.
_risk_before = household_main.knowledge_risk()
household_main.done.add("corpus_written"); household_main._done_changed()
_hedge_known = household_main.knowledge_risk()["hedged_by"]
household_main.open_venture("corpus_written")
_hedge_open = household_main.knowledge_risk()["hedged_by"]
check("building the corpus hedges you; opening it changes nothing",
      _risk_before["hedged_by"] is None and _hedge_known == "corpus_written"
      and _hedge_open == _hedge_known, (_risk_before["hedged_by"], _hedge_known, _hedge_open))
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
_force_sack(household_sack)
household_sack._shocks(household_sack.year)
check("a sacking names the technologies it destroyed",
      any(cause_of(message) == "knowledge_lost" and facts_of(message)["forgotten"]
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


household_dispersed = _corpus_sack_scenario("corpus_dispersed")
_risk_dispersed = household_dispersed.knowledge_risk()
check("corpus_dispersed, closed (not running): `risk` credits its hedge",
      _risk_dispersed["hedged_by"] == "corpus_dispersed"
      and _risk_dispersed["fraction_lost_when_it_happens"]
      == round(household_dispersed.mechanic("corpus_dispersed", "corpus")["fraction_lost"], 2), _risk_dispersed)
_losable_dispersed = _expected_losable(household_dispersed)
household_dispersed._shocks(household_dispersed.year)
_forgotten_dispersed = getattr(household_dispersed, "forgotten", None) or {}
_lost_dispersed = len(_forgotten_dispersed)
check("FAILS IF `risk` AND THE SACK EVER DISAGREE: a closed corpus_dispersed makes "
      "the sack take the fraction `risk` declared",
      _lost_dispersed == max(1, int(len(_losable_dispersed) * _risk_dispersed["fraction_lost_when_it_happens"])), (_lost_dispersed, len(_losable_dispersed)))

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
_goal_messages = [message for _, message in household_goal.log[_log_start:] if cause_of(message) == "knowledge_lost"]
check("the KNOWLEDGE LOST event names how many forgotten technologies stood on the road to the goal",
      bool(_goal_messages) and facts_of(_goal_messages[0])["on_road"] > 0, _goal_messages)
