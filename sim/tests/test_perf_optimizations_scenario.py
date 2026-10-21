"""Scenario: the boolean-only `start_reason(_why=False)` gives the verdict of the explaining one in a running game, and
the fingerprint's `keep_states` toggle changes only what is retained."""

from .harness import *  # noqa: F401,F403


def _start_reason_why_false_boolean_equivalence():
    game = sim(civ="rome_100ad", capital=10000.0)     # the two answers must agree in any state, the opening one included
    mismatches = []
    for node_id in game.order[:200]:
        with_why, _message = game.start_reason(node_id, ignore_trade=True, _why=True)
        without_why, no_message = game.start_reason(node_id, ignore_trade=True, _why=False)
        if with_why != without_why:
            mismatches.append(node_id)
        if no_message is not None:
            mismatches.append("%s_message_not_none" % node_id)
    return not mismatches, "Mismatches found: %s" % mismatches[:5]


slow_check("start_reason _why=False boolean equivalence", _start_reason_why_false_boolean_equivalence)


def _fingerprint_state_retention_toggle():
    from sim.tests import fingerprint as F
    scenario = dict(F.QUICK_SCENARIOS[0], years=1)     # the toggle shows in any run; one year keeps it cheap
    digests_without, _cpu, states_without = F.run(scenario, keep_states=False)
    digests_with, _cpu, states_with = F.run(scenario, keep_states=True)
    return (len(states_without) == 0 and len(states_with) == len(digests_with) and digests_without == digests_with,
            "no_states: %d, with_states: %d" % (len(states_without), len(states_with)))


slow_check("perf_fingerprint keep_states toggle", _fingerprint_state_retention_toggle)
