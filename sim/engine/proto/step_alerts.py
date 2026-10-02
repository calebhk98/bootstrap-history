"""The short ALERTS block at the top of a step report: what a player must not miss."""

# Share of the population lost in one year that counts as an emergency (presentation threshold, not a mechanism).
DEMOGRAPHIC_EMERGENCY_DROP = 0.10
MAX_ALERTS = 6
MAX_ALERT_WIDTH = 110

# (lowercase marker in an event message, label); first match wins per event.
_ALERT_EVENTS = (
    ("credit exhausted", "CREDIT EXHAUSTED"),
    ("close to the limit", "CLOSE TO THE CREDIT LIMIT"),
    ("in arrears, so closed", "CLOSED FOR ARREARS"),
    ("creditors took", "CREDITORS TOOK ASSETS"),
    ("nobody left to keep an eye", "CONCERN UNSTAFFED"),
    ("treasury is looking at your fortune", "TREASURY WATCHING YOUR FORTUNE"),
    ("the state has noticed you", "STATE HAS NOTICED YOU"),
    ("sacked", "SACKED"),
    ("knowledge lost", "KNOWLEDGE LOST"),
    ("abandoned", "ABANDONED"),
    ("bondage", "BONDAGE"),
)


# (alert prefix, severity tier); a lower tier is shown first. Run-ending, sack or regime,
# demographic, economic, project loss, minor setback, then information.
_SEVERITY_BY_PREFIX = (
    ("FOUNDER DIED", 0), ("GOAL REACHED", 0),
    ("SACKED", 1), ("KNOWLEDGE LOST", 1), ("CREDITORS TOOK", 1), ("STATE HAS NOTICED", 1),
    ("BONDAGE", 1), ("POPULATION", 2),
    ("CREDIT EXHAUSTED", 3), ("CLOSED FOR ARREARS", 3), ("CLOSE TO THE CREDIT LIMIT", 3),
    ("LOST", 4), ("ABANDONED", 4),
    ("STOPPED EARLY", 6),
)
_SEVERITY_DEFAULT = 5


def alert_severity(alert):
    """Tier of one alert line; lower is worse."""
    for prefix, tier in _SEVERITY_BY_PREFIX:
        if alert.startswith(prefix):
            return tier
    return _SEVERITY_DEFAULT


def _clip(text):
    return text if len(text) <= MAX_ALERT_WIDTH else text[:MAX_ALERT_WIDTH - 3] + "..."


def demographic_emergency(population_change):
    """The state-screen block for a collapse, or None when the last year was not one."""
    if population_change is None or population_change > -DEMOGRAPHIC_EMERGENCY_DROP:
        return None
    return {"population_change": population_change}


def step_alerts(events, lost, closed_concerns, founder_died, goal_year, stopped_early, population_change, staffing_line=None):
    """One short line per kind of thing that went badly (or won), worst tier first."""
    alerts = []
    if founder_died:
        alerts.append("FOUNDER DIED, aged about %s, in %s" % (founder_died.get("aged_about"), founder_died.get("year")))
    if goal_year is not None:
        alerts.append("GOAL REACHED in %s" % goal_year)
    if demographic_emergency(population_change):
        alerts.append("POPULATION %+.0f%% in the last year" % (100 * population_change))
    seen = {}
    for event in events:
        lowered = event["message"].lower()
        for marker, label in _ALERT_EVENTS:
            if marker in lowered:
                seen.setdefault(label, []).append(event)
                break
    for label, matches in seen.items():
        years = sorted({match["year"] for match in matches})
        extra = " (%d times, %s to %s)" % (len(matches), years[0], years[-1]) if len(matches) > 1 else ""
        alerts.append("%s %s: %s%s" % (label, matches[0]["year"], matches[0]["message"], extra))
    for record in lost:
        alerts.append("LOST %s (%s)" % (record["name"], record["year"]))
    if staffing_line:
        alerts.append(staffing_line)
    elif closed_concerns:
        alerts.append("CLOSED: " + ", ".join(closed_concerns))
    if stopped_early:
        alerts.append("STOPPED EARLY: " + stopped_early)
    alerts.sort(key=alert_severity)
    alerts = [alert if alert is staffing_line else _clip(alert) for alert in alerts]
    if len(alerts) > MAX_ALERTS:
        alerts = alerts[:MAX_ALERTS - 1] + ["... and %d more (see the events below)" % (len(alerts) - MAX_ALERTS + 1)]
    return alerts


def alert_lines(alerts):
    """The rendered block, empty when there is nothing to say."""
    if not alerts:
        return []
    return ["ALERTS (%d)" % len(alerts)] + ["  ! " + alert for alert in alerts]
