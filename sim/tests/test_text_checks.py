"""text_checks: the scanner that finds behaviour checks reading player text (Complaint 515), called on source built here.
The whole-tree list staying empty is `python3 -m sim.tests --text-checks`."""
QUICK_TOPIC = True

from .harness import check
from sim.tests import text_checks

SNIPPETS = {
    "a reply's wording read by a behaviour check":
        ('check("it is refused", "cannot afford" in reply["error"])', None),
    "a log line read by phrase":
        ('check("it is logged", any("has stopped" in line for _year, line in log))', None),
    "a structured read is not text":
        ('check("it is refused", cause_of(reply["error"]) == "cash_short")', False),
    "a key check is not text":
        ('check("it carries the field", "ready_year" in reply)', False),
    "a marked check is presentation":
        ('# presentation: the refusal wording\\ncheck("it says so", "cannot afford" in reply["error"])', "marker"),
    "a not-text mark skips the check":
        ('# not text: a stored label\\ncheck("it is kept", "first result" in cache)', False),
    "a renderer's output is presentation":
        ('screen = render_mines(row)\\ncheck("it prints it", "ready in" in screen)', "renderer"),
}

for label, (source, expected) in SNIPPETS.items():
    found = text_checks.scan_source(source.replace("\\n", "\n"), "fixture")
    if expected is False:
        passed = found == []
    elif expected is None:
        passed = len(found) == 1 and found[0][2] is None
    else:
        passed = len(found) == 1 and found[0][2] == expected
    check(label, passed, found)
