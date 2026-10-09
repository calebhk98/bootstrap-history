"""What mining techniques change in the physical works of a mine. A node
declares a `mine_works` mechanic; the engine collects the specs of the
running ones and `combine` folds them into one effects dict that the works
formulas (mine_works.py, deposits.py) read. Standalone: specs in, dict out.

Fields a spec may carry (all optional, unknown ones are ignored):
  drainage_lift_efficiency   fraction of a labourer's power that becomes
                             water lift in the device; the best running one
                             replaces bailing
  gravity_drained_head_share share of the working depth that drains out by
                             gravity (an adit), so no lift is paid on it; the
                             largest wins
  gravel_moved_multiple      gravel a hydraulic working moves and washes per
                             labourer-hour, relative to the book rate;
                             multiplies
"""
from sim.constants import declare

BAILING_MECHANICAL_EFFICIENCY = declare(
    "BAILING_MECHANICAL_EFFICIENCY", 0.3, kind="temporary_heuristic",
    unit="fraction of labourer power that becomes water lift",
    source="Pliny NH 33.97: bailers stand night and day at Baebelo, handing "
           "buckets up; no measured rate was found.",
    confidence="D",
    why="Hand-passed buckets spill and move the carrier's own weight, so "
        "they lift less per unit of work than a windlass (the hoist figure "
        "in deposits.py); screws and wheels are then measured against it. "
        "Replace with a measured bucket-chain rate.")

DRAINED_HEAD_SHARE_LIMIT = declare(
    "DRAINED_HEAD_SHARE_LIMIT", 0.95, kind="temporary_heuristic",
    unit="largest share of working depth an adit can drain",
    source=None, confidence="D",
    why="The sump below the adit mouth still has to be lifted from; an "
        "adit never drains the whole shaft. The deposit catalogue has no "
        "relief data to derive the adit level from.")


def combine(specs):
    """One effects dict from the `mine_works` specs of the running nodes.
    Only effects that beat the baseline appear; an empty dict changes nothing."""
    effects = {}
    for spec in specs:
        efficiency = spec.get("drainage_lift_efficiency")
        if efficiency is not None and efficiency > BAILING_MECHANICAL_EFFICIENCY:
            effects["drainage_lift_efficiency"] = max(
                effects.get("drainage_lift_efficiency", 0.0), efficiency)
        share = spec.get("gravity_drained_head_share")
        if share:
            effects["gravity_drained_head_share"] = min(
                DRAINED_HEAD_SHARE_LIMIT,
                max(effects.get("gravity_drained_head_share", 0.0), share))
        multiple = spec.get("gravel_moved_multiple")
        if multiple is not None and multiple > 1.0:
            effects["gravel_moved_multiple"] = (
                effects.get("gravel_moved_multiple", 1.0) * multiple)
    return effects


def effects_key(effects):
    """A hashable form of an effects dict, for caches."""
    return tuple(sorted((effects or {}).items()))
