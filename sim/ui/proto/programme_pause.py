"""The conditions a player sets under which a programme stops acting: debt, war risk, a resource shortage."""

from sim.engine.hazard_window import hazards_not_yet_past
from sim.engine.shortage_conditions import condition_rows

PAUSE_KEYS = ("pause_debt", "pause_war_risk", "pause_shortage")


def war_risk(sim):
    """Yearly chance a site is sacked by the hazards running now, after what the founder has built."""
    return sum(sim.hazard_figure("sack_chance", hazard)
               for hazard, _start, _end, in_progress in hazards_not_yet_past(sim.civ, sim.year)
               if in_progress and hazard.get("sack_chance"))


def shortage_loss(sim):
    """(share of planned work lost, material) for the standing shortage, or (0, None)."""
    rows = condition_rows(sim)
    if not rows:
        return 0.0, None
    return 1.0 - rows[0]["throughput"], rows[0]["material"]


def tripped(sim, pauses):
    """Why a player-set pause condition holds now, or None."""
    limit = pauses.get("pause_debt")
    if limit is not None and -sim.capital > limit:
        return "debt over the %s you allowed" % "{:,.0f}".format(limit)
    limit = pauses.get("pause_war_risk")
    risk = war_risk(sim) if limit is not None else 0.0
    if limit is not None and risk > limit:
        return "war risk (%.0f%% a year of a site being sacked) is over the %.0f%% you allowed" % (
            100 * risk, 100 * limit)
    limit = pauses.get("pause_shortage")
    if limit is not None:
        loss, material = shortage_loss(sim)
        if material and loss > limit:
            return "%s shortage (%.0f%% of planned work lost) is over the %.0f%% you allowed" % (
                material, 100 * loss, 100 * limit)
    return None


def pauses_text(programme):
    parts = ["%s %s" % (key, programme["pauses"][key]) for key in PAUSE_KEYS
             if programme.get("pauses", {}).get(key) is not None]
    if parts:
        parts.append("auto-resume" if programme.get("auto_resume") else "stays paused until you resume")
    return ", ".join(parts) or "none"
