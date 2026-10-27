"""Whether a failed attempt can be diagnosed, and what the report says.

A node declares the `diagnosis_instrument` mechanic: the quantity it must
reach (`needed`, in `unit`, larger being worse), the words for it, and the
node whose possession lets a household measure it. Without that node a failure
teaches nothing and says why; with it the report gives the figure reached
against the figure needed.
"""
from typing import Any, Collection, Mapping, Optional

from sim.constants import declare

SHORTFALL_FACTOR_RANGE = declare(
    "SHORTFALL_FACTOR_RANGE", (1.5, 20.0), kind="temporary_heuristic",
    unit="factor by which the measured quantity missed its target",
    source=None, confidence="D",
    why="A failed attempt missed its target purity or tolerance by a factor "
        "drawn uniformly from this range, reported only when a held instrument "
        "can measure it. The sim does not yet model the process quality that "
        "would give the shortfall; the range is a placeholder, not measured.")


def failure_teaches(spec: Optional[Mapping[str, Any]], held: Collection[str]) -> bool:
    """True when a failure of a node declaring `spec` (its `diagnosis_instrument` mechanic, or None) can be diagnosed:
    it needs no instrument, or the household holds the one it names."""
    return spec is None or spec["instrument"] in held


def measured_report(spec: Mapping[str, Any], factor: float, instrument_name: str) -> str:
    """The sentence for a failure measured with the instrument: the figure reached (`factor` times what was needed)
    against the figure needed."""
    reached = spec["needed"] * factor
    return ("Measured with %s: %s reached %.3g %s against %.3g needed (%s)."
            % (instrument_name, spec["quantity"], reached, spec["unit"], spec["needed"], spec["needed_words"]))


def unmeasured_report(spec: Mapping[str, Any], instrument_name: str) -> str:
    """The sentence for a failure nothing held can measure."""
    return ("You cannot tell why: this work needs %s, and nothing you hold can "
            "measure it. %s would. This failure teaches nothing, so the next "
            "attempt is no safer."
            % (spec["needed_words"], instrument_name))
