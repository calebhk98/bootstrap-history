"""text_decisions: no code under sim/ decides on a log line's or a refusal's text (Complaint 521)."""
from .harness import check
from sim.tests import text_decisions

SNIPPETS = {
    "a log line searched for a phrase":
        ('for year, line in sim.log:\n    if "founder dies" in line.lower():\n        pass', 1),
    "a log slice matched by a start":
        ('lines = sim.log[before:]\nfor year, message in lines:\n    if message.startswith("FAILED"):\n        pass', 1),
    "a regex over a reply's message":
        ('age = re.search(r"aged about (\\d+)", event["message"])', 1),
    "a refusal's error compared with a phrase":
        ('if reply.get("error") == "no money":\n    pass', 1),
    "a log line read by its kind":
        ('for year, message in sim.log:\n    if cause_of(message) == "founder_dies":\n        pass', 0),
    "a log line only stored":
        ('for year, message in sim.log:\n    events.append(message)', 0),
    "a marked presentation read":
        ('for year, message in sim.log:\n    # presentation: the player\'s own search\n    if find in message:\n        pass', 0),
    "ids compared in a loop over something else":
        ('for node_id in sim.done:\n    if node_id in need:\n        pass', 0),
}

APPENDS = {
    "a plain string appended to the household log":
        ('household.log.append((year, "you hire a smith"))', 1),
    "a plain name appended to a log":
        ('sim.log.append((sim.year, line))', 1),
    "a line passed to say":
        ('world.say("the loss has eased")', 1),
    "a LogLine appended":
        ('household.log.append((year, LogLine("hired", "you hire a smith")))', 0),
    "a marked pass-through":
        ('household.log.append((year, text))  # plain line: the caller passes a LogLine', 0),
    "a list that is not a log":
        ('rows.append((year, "text"))', 0),
}

for label, (source, expected) in APPENDS.items():
    found = text_decisions.scan_plain_appends(source)
    check(label, len(found) == expected, found)

for label, (source, expected) in SNIPPETS.items():
    found = text_decisions.scan_source(source)
    check(label, len(found) == expected, found)

_found = text_decisions.scan()
check("no code under sim/ decides on a log line's or refusal's text (python3 -m sim.tests --text-decisions)",
      _found == [], _found[:5])

_plain = text_decisions.scan_appends()
check("every append to a log under sim/ is a LogLine with a kind", _plain == [], _plain[:5])
_unlisted = text_decisions.unlisted_kinds()
check("every kind a LogLine is given is listed in sim/ui/proto/event_kinds.py", _unlisted == [], _unlisted)
