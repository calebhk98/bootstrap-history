"""knowledge_loss_and_consequences: complaints 233 (a rebuild keeps what
survives), 237 (failures say what failed, and which risk is live), 238
(effect lines carry before and after), 241 (a BENEFIT block in `why`), 243
(patron death recovery and the scandal trend) and 252 (a visible successor
objective)."""
from .harness import *  # noqa: F401,F403
from sim.engine.data import closure as _closure_of
from sim.ui.proto.techtree import _node_explain
from sim.ui.proto.state import _agent_state_founder
from sim.ui.proto.economy import _agent_portfolio


def _forgotten_sim(node_id, forgotten=True):
    """A society holding every prerequisite of `node_id`; the node itself
    is either never built or (`forgotten`) built and since lost."""
    test_sim = sim(capital=1e10)
    for prerequisite in _closure_of(NODES, node_id) - {node_id}:
        test_sim.done.add(prerequisite)
    test_sim.employees.clear()
    test_sim._done_changed()
    if forgotten:
        test_sim.forgotten[node_id] = test_sim.year - 10
    return test_sim


_plain = sim()   # shared by the checks that only read a game
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

_crew = _forgotten_sim(_NODE)
_crew.done.add("corpus_dispersed")
for _trade in NODES[_NODE]["lab"]:
    _crew.employees[_trade] = 5.0
check("237: living practitioners of the node's trades keep more of it",
      _crew.rebuild_retained_share(_NODE) > _copy.rebuild_retained_share(_NODE),
      (_crew.rebuild_retained_share(_NODE), _copy.rebuild_retained_share(_NODE)))

_plant = _forgotten_sim(_NODE)
_dependents = [node_id for node_id, node in NODES.items() if _NODE in node["pre"]]
for _dependent in _dependents[:3]:
    _plant.done.add(_dependent)
_plant._done_changed()
check("237: surviving plant built on it keeps more of it",
      _plant.rebuild_retained_share(_NODE) > _bare.rebuild_retained_share(_NODE),
      (_plant.rebuild_retained_share(_NODE),))

_explained = _node_explain(_crew, NODES, _NODE)
check("237: `why` says what a rebuild keeps and why",
      "rebuild" in _explained and "forgotten" in str(_explained["rebuild"]).lower()
      and "%" in str(_explained["rebuild"]), _explained.get("rebuild"))
check("237: a node that was never lost carries no rebuild line",
      "rebuild" not in _node_explain(_first, NODES, _NODE))


# --- 241: a failure says what failed, and which risk is live --------------
class _AlwaysFail(random.Random):
    def random(self):
        return 0.0


def _failure_line(test_sim, node_id):
    test_sim.funding_capacity = lambda: 1.0
    test_sim.rng = _AlwaysFail(1)
    test_sim.initialize_project(node_id)
    before = len(test_sim.log)
    test_sim._complete(node_id)
    return " ".join(message for _year, message in test_sim.log[before:])


_science = next(node_id for node_id, node in NODES.items()
                if node.get("kind") == "SCIENCE" and node["risk"] and not node["mat"])
_engineering = next(node_id for node_id, node in NODES.items()
                    if node.get("kind") == "ENGINEERING" and node["risk"] and node["mat"]
                    and node["lab"])
_science_line = _failure_line(sim(capital=1e10), _science)
_engineering_line = _failure_line(sim(capital=1e10), _engineering)
check("241: a failed science node names a teaching or adoption failure",
      "what failed" in _science_line.lower()
      and ("teach" in _science_line or "adopt" in _science_line), _science_line)
check("241: a failed engineering node names its apparatus and materials",
      "what failed" in _engineering_line.lower()
      and "apparatus" in _engineering_line
      and sorted(NODES[_engineering]["mat"])[0].split("_")[0] in _engineering_line,
      _engineering_line)
_active_sim = sim(capital=1e10)
_active_sim.failed_attempts[_engineering] = 2
_active_sim.initialize_project(_engineering)
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
_effect_sim = sim()
_effect_before = float(_effect_sim.civ["literacy_general"])
_effect_sim.done.add(_effect_node)
_effect_sim.apply_tech_effects(_effect_node)
_effect_text = " ".join(message for _year, message in _effect_sim.log
                        if "changes the society" in message)
_effect_after = float(_effect_sim.civ["literacy_general"])
check("242: a literacy effect names the old and new value",
      "literacy_general" in _effect_text
      and "%.1f%%" % (_effect_before * 100) in _effect_text
      and "%.1f%%" % (_effect_after * 100) in _effect_text, _effect_text)
_disease_node = next(node_id for node_id in _plain.DISEASE_BURDEN_TECH_IDS
                     if node_id not in _plain.done and node_id not in _plain.coverage_nodes())
_disease_sim = sim()
_burden_before = _disease_sim._disease_burden()
_disease_sim.done.add(_disease_node)
_disease_sim._done_changed()
_disease_sim.apply_tech_effects(_disease_node)
_burden_after = _disease_sim._disease_burden()
_disease_text = " ".join(message for _year, message in _disease_sim.log
                         if "changes the society" in message)
check("242: a population effect names the disease burden before and after",
      "population" in _disease_text and "%.2f" % _burden_before in _disease_text
      and "%.2f" % _burden_after in _disease_text, _disease_text)

# --- 245: a BENEFIT block in `why` ----------------------------------------
_school = _node_explain(_plain, NODES, "school_founded")
_benefit = _school.get("benefit") or {}
check("245: a service node's `why` has a BENEFIT block with the four labelled parts",
      all(key in _benefit for key in
          ("permanent", "while_open", "cost_of_opening", "if_shut")), _benefit)
check("245: ...the while-open part is the engine's own lost-benefit text",
      "training" in str(_benefit.get("while_open", "")).lower(), _benefit)
check("245: ...and the cost of opening names a yearly figure",
      any(character.isdigit() for character in str(_benefit.get("cost_of_opening", ""))),
      _benefit)
_corpus = _node_explain(_plain, NODES, "corpus_written").get("benefit") or {}
check("245: the corpus says its hedge holds while shut and its standing needs it open",
      "hedge" in str(_corpus.get("permanent", "")).lower()
      and "tanding" in str(_corpus.get("while_open", "")), _corpus)
_vaccination = next(node_id for node_id in _plain.DISEASE_BURDEN_TECH_IDS if node_id not in _plain.coverage_nodes())
_vaccination_benefit = _node_explain(_plain, NODES, _vaccination).get("benefit") or {}
check("245: a knowledge node says its effect is permanent and needs no concern open",
      "permanent" in _vaccination_benefit
      and "disease" in str(_vaccination_benefit["permanent"]).lower(), _vaccination_benefit)


# --- 247: a patron's death says what recovers and is not a yearly trend ---
class _EventsRng(random.Random):
    """Draws low for the first roll (the patron) and high for the rest."""
    def __init__(self):
        super().__init__(1)
        self.calls = 0

    def random(self):
        self.calls += 1
        return 0.0 if self.calls == 1 else 0.99


_patron_sim = sim(capital=1e10)
run_it(_patron_sim, "patron_local")
_patron_sim.protection = 0.9
_patron_sim.scandal_last_year = _patron_sim.scandal
_patron_sim.rng = _EventsRng()
_scandal_before = _patron_sim.scandal
_patron_sim._random_events(_patron_sim.year)
_patron_line = " ".join(message for _year, message in _patron_sim.log if "patron dies" in message)
check("247: the death line says what brings protection back and when",
      "recount" in _patron_line and "heir" in _patron_line, _patron_line)
check("247: set-up: scandal did jump",
      _patron_sim.scandal - _scandal_before >= _patron_sim.PATRON_DEATH_SCANDAL - 1e-9)
_patron_state = S._agent_state(_patron_sim, NODES)
check("247: a one-off scandal jump is not extrapolated into a trend",
      _patron_state["years_until_scandal_crosses_the_line"] is None
      and (_patron_state["scandal_rose_by_last_year"] or 0.0) < 0.05,
      (_patron_state["years_until_scandal_crosses_the_line"],
       _patron_state["scandal_rose_by_last_year"]))
_policy_reply = S._agent_dispatch(_plain, NODES, {"cmd": "policy"})
_heir_description = _policy_reply["what_each_does"]["auto_court_heir"]
check("247: auto_court_heir describes the by-hand route", "bribe" in _heir_description,
      _heir_description)

# --- 256: a named, visible successor objective ----------------------------
_deputy_sim = _plain
_deputy_sim.directors_extra = 0.2
_succession = _agent_state_founder(_deputy_sim).get("succession") or {}
check("256: state shows the deputy count, their hours and whether they carry the work",
      _succession.get("deputies") == 0.2 and _succession.get("deputy_hours_a_year")
      and _succession.get("deputies_carry_the_work") is False, _succession)
check("256: ...and a named objective with the gap and where deputies come from",
      "train a successor" in str(_succession.get("objective", "")).lower()
      and "more" in str(_succession.get("objective", "")), _succession)
_deputy_sim.directors_extra = 5.0
_covered = _agent_state_founder(_deputy_sim).get("succession") or {}
check("256: once deputies carry the work the objective says it is met",
      _covered.get("deputies_carry_the_work") is True
      and "met" in str(_covered.get("objective", "")), _covered)
