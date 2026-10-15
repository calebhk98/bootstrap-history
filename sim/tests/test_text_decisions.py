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

for label, (source, expected) in SNIPPETS.items():
    found = text_decisions.scan_source(source)
    check(label, len(found) == expected, found)

_found = text_decisions.scan()
check("no code under sim/ decides on a log line's or refusal's text (python3 -m sim.tests --text-decisions)",
      _found == [], _found[:5])
