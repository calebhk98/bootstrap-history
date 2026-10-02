"""`treetool.py merge` must not lose anything a branch author wrote.

Complaints/52. The merge refuses to write while any event would drop a
requirement. Unknown trades, unresolvable prerequisites, dependency cycles and
undeclared materials must all be zero.
"""
import collections
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

ZERO_CATEGORIES = ("unknown_trade", "unresolvable_prerequisite", "material_is_technology", "dependency_cycle")


def measure_merge_events():
    """{category: [message, ...]} from a dry-run merge."""
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "sim", "treetool.py"), "merge", "--dry-run"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    events = collections.defaultdict(list)
    category = None
    for line in result.stdout.splitlines():
        header = re.match(r"  (\w+) \(\d+\)$", line)
        if header:
            category = header.group(1)
        elif category and line.startswith("     "):
            events[category].append(line.strip())
    return events


def measure_undeclared_counts(events):
    counts = collections.Counter()
    for message in events.get("undeclared_material", []):
        match = re.search(r"UNDECLARED material '([^']+)'", message)
        counts[match.group(1)] += 1
    return counts


class BranchMergeBlockingEventTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.events = measure_merge_events()

    def test_no_unknown_trades_prerequisites_or_cycles(self):
        for category in ZERO_CATEGORIES:
            self.assertEqual(self.events.get(category, []), [], (
                "merge --dry-run reports %s events. Fix the branch source "
                "(trade name, prerequisite id, or the cycle edge)."
                % category))

    def test_no_undeclared_material(self):
        counts = measure_undeclared_counts(self.events)
        self.assertEqual(dict(counts), {}, (
            "Undeclared material events: %s. Add a production recipe "
            "in data/production/, or rename the material in the branch." % dict(counts)))


if __name__ == "__main__":
    unittest.main()
