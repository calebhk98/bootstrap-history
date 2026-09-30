"""The escalated warning for a sacking window that is close or running.

Reads `knowledge_risk` (the numbers `risk` prints) and the hedge table
`corpus_hedge` uses, so this screen and `risk` cannot disagree.
"""

from .data import closure

# Years before a window opens at which the warning starts to be shown.
WARNING_HORIZON_YEARS = 30


def _hedge_options(sim):
    """Hedges stronger than the one held, each with its distance and cost."""
    options = []
    for hedge_id, _chance, fraction_lost in sim.corpus_hedge_tiers():
        if sim.has(hedge_id):
            break
        if hedge_id not in sim.nodes or (sim.fog and not sim.is_visible(hedge_id)):
            continue
        missing = [node_id for node_id in closure(sim.nodes, hedge_id)
                   if node_id not in sim.done]
        options.append({"id": hedge_id, "name": sim.nodes[hedge_id]["name"],
                        "steps_away": len(missing),
                        "cost": round(sum(sim.project_cost(node_id) for node_id in missing), 1),
                        "fraction_lost_once_built": fraction_lost})
    return options


def knowledge_loss_warning(sim):
    """None, or the nearest sacking window within the horizon (or running),
    the expected loss per sack, and the cheapest hedge still to build."""
    risk = sim.knowledge_risk()
    windows = []
    for hazard in risk.get("known_hazards_ahead") or []:
        if not hazard.get("sacks_a_site"):
            continue
        year_start, year_end = hazard["years"][0], hazard["years"][-1]
        in_progress = year_start <= sim.year <= year_end
        years_until = 0 if in_progress else year_start - sim.year
        if years_until <= WARNING_HORIZON_YEARS:
            windows.append((years_until, hazard, in_progress))
    if not windows:
        return None
    years_until, hazard, in_progress = min(windows, key=lambda entry: entry[0])
    options = _hedge_options(sim)
    if not options:
        return None
    cheapest = min(options, key=lambda option: (option["cost"], option["steps_away"]))
    at_risk = risk["technologies_at_risk"]
    if not at_risk:
        return None
    cheapest["expected_technologies_lost_per_sacking_once_built"] = round(
        at_risk * cheapest.pop("fraction_lost_once_built"), 1)
    return {"name": hazard["name"], "years": hazard["years"],
            "years_until": years_until, "in_progress": in_progress,
            "technologies_at_risk": at_risk,
            "expected_technologies_lost_per_sacking":
                risk["expected_technologies_lost_per_sacking"],
            "cheapest_hedge": cheapest}


def warning_lines(warning):
    """The prominent text line for `state` and `path`."""
    if not warning:
        return []
    hedge = warning["cheapest_hedge"]
    when = ("is under way now" if warning["in_progress"]
            else "opens in %d year%s" % (warning["years_until"],
                                         "" if warning["years_until"] == 1 else "s"))
    return ["!! WARNING: %s sacking window %d-%d %s. Each sack is expected to cost you "
            "%s of your %s technologies. Cheapest hedge: %s, %d step%s away, about %s "
            "denarii; built, it would cut that to %s. 'risk' has the detail."
            % (warning["name"], warning["years"][0], warning["years"][-1], when,
               _number(warning["expected_technologies_lost_per_sacking"]),
               _number(warning["technologies_at_risk"]), hedge["id"],
               hedge["steps_away"], "" if hedge["steps_away"] == 1 else "s",
               _number(hedge["cost"]),
               _number(hedge["expected_technologies_lost_per_sacking_once_built"]))]


def _number(value):
    return "{:,.0f}".format(value) if abs(value) >= 100 else "{:,.1f}".format(value).rstrip("0").rstrip(".")
