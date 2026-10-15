"""Severity tiers for the event stream: how much a line should weigh on the reader. Lower tier is worse.

The tier of an event is the tier its kind is listed under (event_kinds.py); an event with no listed kind is informational.
"""
from .event_kinds import TIER_NAMES, tier_name

# Text-screen marker per tier.
_MARKERS = ("***", "***", "!!", "!!", "!!", "!", "", "")


def event_tier(event):
    """Index into TIER_NAMES for one log line or reply event."""
    return TIER_NAMES.index(tier_name(event))


def tag_events(events):
    """Copies of the events, each with its tier name under `severity`."""
    return [{**event, "severity": tier_name(event)} for event in events or []]


def order_events(events):
    """Worst tier first; events of one tier keep their order."""
    return sorted(events or [], key=event_tier)


def event_marker(event):
    """The prefix a text screen puts on the event's line ('' for quiet ones)."""
    return _MARKERS[event_tier(event)]
