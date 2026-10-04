"""The merge of the branch files must not lose anything a branch author wrote.

Complaints/52. The merge refuses to write while any event would drop a
requirement. Unknown trades, unresolvable prerequisites, dependency cycles and
undeclared materials must all be zero.
"""
import collections
import re
import unittest

from sim.engine import tree_merge

ZERO_CATEGORIES = ("unknown_trade", "unresolvable_prerequisite", "material_is_technology", "dependency_cycle")


def measure_merge_events():
    """{category: [message, ...]} from one merge of the real branch files."""
    events = collections.defaultdict(list)
    for category, message in tree_merge.build_tree().losses:
        events[category].append(message)
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
                "the merge reports %s events. Fix the branch source "
                "(trade name, prerequisite id, or the cycle edge)."
                % category))

    def test_no_undeclared_material(self):
        counts = measure_undeclared_counts(self.events)
        self.assertEqual(dict(counts), {}, (
            "Undeclared material events: %s. Add a production recipe "
            "in data/production/, or rename the material in the branch." % dict(counts)))


if __name__ == "__main__":
    unittest.main()
