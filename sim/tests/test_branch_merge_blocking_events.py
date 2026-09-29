"""`treetool.py merge --dry-run` must not lose anything a branch author wrote.

Complaints/54. The merge refuses to write while any event would drop a
requirement. Unknown trades, unresolvable prerequisites and dependency cycles
must stay at zero. Undeclared materials still block, and each remaining name is
pinned with its event count. The pin fails in both directions: a new name (or a
higher count) is a regression, and a cleared name asks to be un-pinned so the
list can only shrink.
"""
import collections
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# Materials that branch nodes name and no production recipe makes.
# Each needs a recipe with a physical yield, or a node edit; none may be guessed.
KNOWN_UNDECLARED_MATERIALS = {
}

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
                "(trade alias in data/branches/ALIASES.json, prerequisite id, or the cycle edge)."
                % category))

    def test_no_new_undeclared_material(self):
        counts = measure_undeclared_counts(self.events)
        worse = {name: count for name, count in counts.items()
                 if count > KNOWN_UNDECLARED_MATERIALS.get(name, 0)}
        self.assertEqual(worse, {}, (
            "New undeclared material events: %s. Add a production recipe "
            "in data/production/ or alias the name in data/branches/ALIASES.json." % worse))

    def test_a_cleared_material_lowers_the_pin(self):
        counts = measure_undeclared_counts(self.events)
        cleared = {name: pinned for name, pinned in KNOWN_UNDECLARED_MATERIALS.items()
                   if counts.get(name, 0) < pinned}
        self.assertEqual(cleared, {}, (
            "Cleared or reduced: %s. Lower KNOWN_UNDECLARED_MATERIALS so the "
            "count can only go down." % cleared))


if __name__ == "__main__":
    unittest.main()
