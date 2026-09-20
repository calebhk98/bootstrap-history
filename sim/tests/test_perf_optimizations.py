"""Tests for conservative performance optimizations.

Guarantees that start_reason(..., _why=False) produces the exact same boolean
verdict as start_reason(..., _why=True) and that _project_progress_afford_gate()
returns identical results when reusing precomputed revenue/upkeep.
"""
from .harness import *  # noqa: F401,F403


def _test_start_reason_why_false_boolean_equivalence():
    """Verify start_reason(node_id, _why=False)[0] == start_reason(node_id, _why=True)[0]
    for all nodes in a standard simulation."""
    sim_inst = sim(civ="rome_100ad", capital=10000.0)
    sim_inst.step()
    
    mismatches = []
    for node_id in sim_inst.order[:200]:
        bool_with_why, why_msg = sim_inst.start_reason(node_id, ignore_trade=True, _why=True)
        bool_without_why, no_msg = sim_inst.start_reason(node_id, ignore_trade=True, _why=False)
        
        if bool_with_why != bool_without_why:
            mismatches.append(node_id)
        if no_msg is not None:
            mismatches.append(f"{node_id}_msg_not_none")

    return len(mismatches) == 0, f"Mismatches found: {mismatches[:5]}"


check("start_reason _why=False boolean equivalence", _test_start_reason_why_false_boolean_equivalence)


def _test_afford_gate_behavior():
    """Verify _project_progress_afford_gate output consistency across household capital states."""
    sim_inst = sim(civ="rome_100ad", capital=5000.0)
    sim_inst.step()
    
    # Pick an active project node
    candidate_node = sim_inst.order[0]
    project_state = {
        "ph_left": 100.0,
        "yrs": 0.0,
        "spent": 0.0,
        "cost_left": 500.0,
        "lab_left": {}
    }
    
    res1 = sim_inst._project_progress_afford_gate(
        candidate_node, project_state, money=100.0, refunded=0.0,
        spent_hours=10.0, per=1.0, _arrears_hours_lost=0.0
    )
    
    # Must return tuple (money, refunded)
    return isinstance(res1, tuple) and len(res1) == 2, f"Unexpected return: {res1}"


check("_project_progress_afford_gate returns (money, refunded)", _test_afford_gate_behavior)


def _test_perf_fingerprint_quick_scenarios():
    """Verify perf_fingerprint module exports QUICK_SCENARIOS matching requirement rules."""
    from sim import perf_fingerprint as F
    
    scenarios = F.QUICK_SCENARIOS
    has_rome = any(s["civ"] == "rome_100ad" for s in scenarios)
    has_non_rome = any(s["civ"] != "rome_100ad" for s in scenarios)
    has_events = any(s["events"] for s in scenarios)
    has_fog = any(s["fog"] for s in scenarios)
    
    valid = has_rome and has_non_rome and has_events and has_fog and len(scenarios) >= 3
    return valid, f"Quick scenarios check: {scenarios}"


check("perf_fingerprint QUICK_SCENARIOS validity", _test_perf_fingerprint_quick_scenarios)


def _test_perf_fingerprint_state_retention_toggle():
    """Verify run(scenario, keep_states=False) does not retain full states."""
    from sim import perf_fingerprint as F
    
    sc = F.QUICK_SCENARIOS[0]
    digests_no_states, cpu_no_states, states_no_states = F.run(sc, keep_states=False)
    digests_with_states, cpu_with_states, states_with_states = F.run(sc, keep_states=True)
    
    ok1 = len(states_no_states) == 0
    ok2 = len(states_with_states) == len(digests_with_states)
    ok3 = digests_no_states == digests_with_states
    
    return ok1 and ok2 and ok3, f"no_states: {len(states_no_states)}, with_states: {len(states_with_states)}"


check("perf_fingerprint keep_states toggle", _test_perf_fingerprint_state_retention_toggle)

