"""The refusals of a project that needs trained scholars or craftsmen the household cannot field."""
from sim.agents.api import research_gate


def scholar_gate_text(needed, available, advice_for):
    """None when `available` scholar hands cover `needed`; otherwise the refusal, ending in `advice_for(deficit)`
    where the deficit is the people short."""
    deficit = research_gate.hands_short(needed, available)
    if deficit <= 0.0:
        return None
    return ("needs %d trained scholars, and you have %.1f - counting people on your staff and yourself, plus any "
            "hours already bought under contract as that share of one more. %s" % (needed, available, advice_for(deficit)))


def craftsmen_gate_text(needed, available, advice_for):
    """As `scholar_gate_text`, for craftsmen (staff only, and hours under contract as a share of one more)."""
    deficit = research_gate.hands_short(needed, available)
    if deficit <= 0.0:
        return None
    return ("needs %d trained craftsmen, and you have %.1f - counting people on your staff plus any hours already "
            "bought under contract as that share of one more. %s" % (needed, available, advice_for(deficit)))
