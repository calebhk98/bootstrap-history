"""Severity tiers for the event stream: how much a line should weigh on the
reader. Lower tier is worse; the first tier with a matching marker wins."""

TIER_NAMES = ("run_ending", "regime_war_or_sack", "demographic_catastrophe",
              "economic_crisis", "major_project_failure", "minor_setback",
              "project_completion", "informational")

# Lowercase markers in an event message, per tier, worst tier first.
_TIER_MARKERS = (
    ("run ends", "founder dies", "founder has died", "goal reached"),
    ("sacked", "sack of", "proscri", "the state has noticed you", "bondage",
     "at war", "invaded", "invasion", "overthrown", "conquered"),
    ("famine", "plague", "pestilence", "epidemic", "population still", "starv"),
    ("credit exhausted", "close to the limit", "in arrears", "creditors took",
     "insolvency", "treasury is looking", "you cannot pay everyone"),
    ("abandoned", "knowledge lost", "nobody left to keep an eye", "fire in the", "halted"),
    ("failed", "short of", "directed hours unused", "mothballed", "banditry",
     "prominence", "being talked about", "conspicuous"),
    ("completed", "achieved"),
)
_INFORMATIONAL = len(TIER_NAMES) - 1
# Text-screen marker per tier.
_MARKERS = ("***", "***", "!!", "!!", "!!", "!", "", "")


def event_tier(message):
    """Index into TIER_NAMES for one event message."""
    lowered = str(message).lower()
    for tier, markers in enumerate(_TIER_MARKERS):
        if any(marker in lowered for marker in markers):
            return tier
    return _INFORMATIONAL


def tag_events(events):
    """Copies of the events, each with its tier name under `severity`."""
    return [{**event, "severity": TIER_NAMES[event_tier(event.get("message"))]}
            for event in events or []]


def order_events(events):
    """Worst tier first; events of one tier keep their order."""
    return sorted(events or [], key=lambda event: event_tier(event.get("message")))


def event_marker(message):
    """The prefix a text screen puts on the event's line ('' for quiet ones)."""
    return _MARKERS[event_tier(message)]
