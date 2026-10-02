"""Whether a failed attempt can be diagnosed, and what the report says.

A node declares the `diagnosis_instrument` mechanic: the quantity it must
reach (`needed`, in `unit`, larger being worse), the words for it, and the
node whose possession lets a household measure it. Without that node a failure
teaches nothing and says why; with it the report gives the figure reached
against the figure needed.
"""
from sim.constants import declare

SHORTFALL_FACTOR_RANGE = declare(
    "SHORTFALL_FACTOR_RANGE", (1.5, 20.0), kind="temporary_heuristic",
    unit="factor by which the measured quantity missed its target",
    source=None, confidence="D",
    why="A failed attempt missed its target purity or tolerance by a factor "
        "drawn uniformly from this range, reported only when a held instrument "
        "can measure it. The sim does not yet model the process quality that "
        "would give the shortfall; the range is a placeholder, not measured.")


def _spec(sim, node_id):
    return sim.mechanic(node_id, "diagnosis_instrument")


def failure_teaches(sim, node_id):
    """True when a failure of this node can be diagnosed: it needs no
    instrument, or the household holds the one it names."""
    spec = _spec(sim, node_id)
    return spec is None or spec["instrument"] in sim.state.projects.done


def note_failure(sim, node_id):
    """Record a failure that was or was not diagnosable and return the
    sentence for the report ("" when the node needs no instrument)."""
    spec = _spec(sim, node_id)
    if spec is None:
        return ""
    if failure_teaches(sim, node_id):
        low, high = SHORTFALL_FACTOR_RANGE
        reached = spec["needed"] * sim.rng.uniform(low, high)
        return ("Measured with %s: %s reached %.3g %s against %.3g needed (%s)."
                % (sim.nodes[spec["instrument"]]["name"], spec["quantity"],
                   reached, spec["unit"], spec["needed"], spec["needed_words"]))
    uninformed = sim.state.projects.uninformed_failures
    uninformed[node_id] = uninformed.get(node_id, 0) + 1
    return ("You cannot tell why: this work needs %s, and nothing you hold can "
            "measure it. %s would. This failure teaches nothing, so the next "
            "attempt is no safer."
            % (spec["needed_words"], sim.nodes[spec["instrument"]]["name"]))
