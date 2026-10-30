"""Which running concern the staffing rule would shut next, and how much slack stands between: plain arithmetic on the
numbers handed in (the Sim method `staffing_closure_warnings` gathers them)."""
from typing import Any, Callable, Dict, List, Sequence, Tuple

HANDS_EPSILON = 0.005
NO_ROOM = 0.05


def _trim(amount: float) -> str:
    return ("%.2f" % amount).rstrip("0").rstrip(".")


def staffing_warning_rows(concerns: Sequence[Dict[str, Any]], scholars_held: float, craftsmen_held: float,
                          hired_scholars: float, hired_craftsmen: float, scholars_used: float, craftsmen_used: float,
                          founder_fixed: bool, slack: float, band: float, no_slack_band: float, limit: int,
                          fix_for: Callable[[str], str], cost_words: Callable[[float], str]) -> List[Dict[str, Any]]:
    """The warnings for the running `concerns` (each {"id", "name", "revenue", "upkeep", "hands": (scholars, craftsmen)}).

    Room is the people held (the founder included) plus `slack`, less the people running concerns use, in full-time
    equivalents; it is reported for whichever of a concern's own two kinds of hands is scarcer. Silent while both pools have
    more than `band` of room. Concerns are ranked as the staffing rule would close them, dearest to keep for what they tie up
    first. A founder who cannot leave leaves only the hired people to lose, so a pool whose room survives losing every hired
    person is no risk."""
    scholar_room = scholars_held + slack - scholars_used
    craftsman_room = craftsmen_held + slack - craftsmen_used
    if scholar_room > band and craftsman_room > band:
        return []
    holders = [concern for concern in concerns
               if concern["hands"][1] > HANDS_EPSILON or concern["hands"][0] > HANDS_EPSILON]
    ranked = sorted(holders, key=lambda concern: ((concern["revenue"] - concern["upkeep"]) / max(0.01, concern["hands"][1]),
                                                  -concern["hands"][1]))
    rows: List[Dict[str, Any]] = []
    for concern in ranked:
        scholars_needed, craftsmen_needed = concern["hands"]
        candidates: List[Tuple[str, float]] = []
        if scholars_needed > HANDS_EPSILON and not (founder_fixed and scholar_room - hired_scholars >= 0):
            candidates.append(("scholars", scholar_room))
        if craftsmen_needed > HANDS_EPSILON and not (founder_fixed and craftsman_room - hired_craftsmen >= 0):
            candidates.append(("craftsmen", craftsman_room))
        if not candidates:
            continue
        word, room = min(candidates, key=lambda candidate: candidate[1])
        if room > band:
            continue
        net = max(0.0, concern["revenue"] - concern["upkeep"])
        cost = cost_words(net)
        fix = fix_for("scholars" if word == "scholars" else "artisans")
        one_loss_closes = room <= no_slack_band + 1e-9
        name = concern["name"]
        if room <= NO_ROOM:
            headline = ("%s has no %s free this year and is next in line to close - that would cost %s in recurring income. %s"
                        % (name, word, cost, fix))
        elif one_loss_closes:
            headline = ("%s has no spare %s: losing just one more closes it outright, costing %s in recurring income. %s"
                        % (name, word, cost, fix))
        else:
            headline = "%s has %s spare %s before it closes" % (name, ("%.1f" % room).rstrip("0").rstrip("."), word)
        held, in_use = (scholars_held, scholars_used) if word == "scholars" else (craftsmen_held, craftsmen_used)
        explained = ("spare %s = %s held (you included) + %s allowed before a closure - "
                     "%s in use by running concerns, all in full-time equivalents; a "
                     "concern ties up a share of a person's year, so spare is not a headcount"
                     % (word, _trim(held), _trim(slack), _trim(in_use)))
        rows.append({"id": concern["id"], "name": name, "within": round(max(0.0, room), 1),
                     "of": word, "headline": headline, "held": round(held, 2),
                     "in_use": round(in_use, 2), "allowance": slack, "explained": explained,
                     "recurring_income_at_risk": round(net, 1),
                     "one_loss_closes_it": one_loss_closes,
                     "fix": fix})
        if len(rows) >= limit:
            break
    return rows
