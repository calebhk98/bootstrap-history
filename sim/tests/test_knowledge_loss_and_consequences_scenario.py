"""SCENARIO: in a game, complaints 241 (the portfolio shows the live risk), 242 (effect lines carry before and after),
247 (a patron's death is not extrapolated into a scandal trend) and 256 (a visible successor objective). The rebuild
share rule is in `test_knowledge_loss_and_consequences`."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of
from sim.engine.data import closure as _closure_of
from sim.ui.proto.state import _agent_state_founder
from sim.ui.proto.economy import _agent_portfolio


def _forgotten_sim(node_id, forgotten=True):
    """A society holding every prerequisite of `node_id`; the node itself
    is either never built or (`forgotten`) built and since lost."""
    test_sim = unopened_sim(capital=1e10)
    for prerequisite in _closure_of(NODES, node_id) - {node_id}:
        test_sim.done.add(prerequisite)
    test_sim.employees.clear()
    test_sim._done_changed()
    if forgotten:
        test_sim.forgotten[node_id] = test_sim.year - 10
    return test_sim


_plain = unopened_sim()   # shared by the checks that only read a game

_NODE = "blast_furnace"
_first = _forgotten_sim(_NODE, forgotten=False)
_bare = _forgotten_sim(_NODE)

# --- 237: a rebuild keeps what survives, derived from state ---------------
check("237: a forgotten node with nothing surviving costs what a first build does",
      abs(_bare.project_cost_without_materials(_NODE)
          - _first.project_cost_without_materials(_NODE)) < 1e-6
      and _bare.payment_schedule_years(_NODE) == _first.payment_schedule_years(_NODE),
      (_bare.rebuild_retained_share(_NODE),))

_copy = _forgotten_sim(_NODE)
_copy.done.add("corpus_dispersed")
_copy._done_changed()
check("237: a dispersed copy of the corpus makes the rebuild cheaper than a first build",
      _copy.project_cost_without_materials(_NODE)
      < _first.project_cost_without_materials(_NODE)
      and _copy.payment_schedule_years(_NODE) < _first.payment_schedule_years(_NODE),
      (_copy.rebuild_retained_share(_NODE),))
_copy_record = _copy.initialize_project(_NODE)
check("237: ...and fewer of the founder's hours are still to do",
      _copy_record["ph_left"] < NODES[_NODE]["ph"], _copy_record["ph_left"])


# --- 241: a failure says what failed, and which risk is live --------------
_engineering = next(node_id for node_id, node in NODES.items()
                    if node.get("kind") == "ENGINEERING" and node["risk"] and node["mat"]
                    and node["lab"])
_active_sim = unopened_sim(capital=1e10)
_active_sim.initialize_project(_engineering)
for _attempt in range(2):
    _active_sim.learn_from_failed_attempt(_engineering)
_portfolio = _agent_portfolio(_active_sim, NODES)["projects"][0]
check("241: portfolio shows the live risk, labelled, beside the first-attempt risk",
      abs(_portfolio["chance_of_failure"] - _active_sim.effective_risk(_engineering)) < 1e-9
      and _portfolio["chance_of_failure_before_any_attempt"] == NODES[_engineering]["risk"]
      and _portfolio["chance_of_failure"] < NODES[_engineering]["risk"],
      _portfolio)

# --- 242: effect lines carry before and after, and the reach --------------
_effect_node = next(node_id for node_id in sorted(S.TECH_EFFECTS)
                    if "literacy_general" in S.TECH_EFFECTS[node_id]
                    and node_id in NODES and node_id not in _plain.done)
_effect_sim = unopened_sim()
_effect_before = float(_effect_sim.literacy("literacy_general"))
_effect_sim.done.add(_effect_node)
_effect_sim.apply_tech_effects(_effect_node)
_effect_lines = [message for _year, message in _effect_sim.log if cause_of(message) == "society_changed"]
_effect_after = float(_effect_sim.literacy("literacy_general"))
check("242: a literacy effect names the old and new value",
      any(abs(facts_of(line)["changes"]["literacy_general"][0] - _effect_before) < 1e-9
          and abs(facts_of(line)["changes"]["literacy_general"][1] - _effect_after) < 1e-9
          for line in _effect_lines if "literacy_general" in facts_of(line)["changes"]), _effect_lines)
_disease_node = next(node_id for node_id in _plain.DISEASE_BURDEN_TECH_IDS
                     if node_id not in _plain.done and node_id not in _plain.coverage_nodes())
_disease_sim = unopened_sim()
_burden_before = _disease_sim._disease_burden()
_disease_sim.done.add(_disease_node)
_disease_sim._done_changed()
_disease_sim.apply_tech_effects(_disease_node)
_burden_after = _disease_sim._disease_burden()
_disease_lines = [message for _year, message in _disease_sim.log if cause_of(message) == "society_changed"]
check("242: a population effect names the disease burden before and after",
      any(abs(facts_of(line)["changes"]["population"][0] - _burden_before) < 0.005
          and abs(facts_of(line)["changes"]["population"][1] - _burden_after) < 0.005
          for line in _disease_lines if "population" in facts_of(line)["changes"]), _disease_lines)

# --- 247: a patron's death says what recovers and is not a yearly trend ---
class _EventsRng(random.Random):
    """Draws low for the first roll (the patron) and high for the rest."""
    def __init__(self):
        super().__init__(1)
        self.calls = 0

    def random(self):
        self.calls += 1
        return 0.0 if self.calls == 1 else 0.99


_patron_sim = unopened_sim(capital=1e10)
run_it(_patron_sim, "patron_local")
_patron_sim.protection = 0.9
_patron_sim.scandal_last_year = _patron_sim.scandal
_patron_sim.rng = _EventsRng()
_scandal_before = _patron_sim.scandal
_patron_sim._random_events(_patron_sim.year)
check("247: set-up: scandal did jump",
      _patron_sim.scandal - _scandal_before >= _patron_sim.PATRON_DEATH_SCANDAL - 1e-9)
_patron_state = S._agent_state(_patron_sim, NODES)
check("247: a one-off scandal jump is not extrapolated into a trend",
      _patron_state["years_until_scandal_crosses_the_line"] is None
      and (_patron_state["scandal_rose_by_last_year"] or 0.0) < 0.05,
      (_patron_state["years_until_scandal_crosses_the_line"],
       _patron_state["scandal_rose_by_last_year"]))
# --- 256: a named, visible successor objective ----------------------------
_deputy_sim = _plain
_deputy_sim.directors_extra = 0.2
_succession = _agent_state_founder(_deputy_sim).get("succession") or {}
check("256: state shows the deputy count, their hours and whether they carry the work",
      _succession.get("deputies") == 0.2 and _succession.get("deputy_hours_a_year")
      and _succession.get("deputies_carry_the_work") is False, _succession)
_deputy_sim.directors_extra = 5.0
_covered = _agent_state_founder(_deputy_sim).get("succession") or {}
check("256: once deputies carry the work the state says so",
      _covered.get("deputies_carry_the_work") is True, _covered)
