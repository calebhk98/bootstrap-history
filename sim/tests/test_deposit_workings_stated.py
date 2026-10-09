"""Every gold and silver deposit states its working: a date and a size, or why they are unknown.

Nothing is guessed to fill a gap (CLAUDE.md 4.1); a deposit with neither is a hole in the data."""

QUICK_TOPIC = True

import json
import os
import unittest

DEPOSITS = os.path.join(os.path.dirname(__file__), "..", "..", "data", "world", "geography", "deposits")
PRECIOUS = ("gold", "silver")


def precious_deposits():
    rows = []
    for name in sorted(os.listdir(DEPOSITS)):
        with open(os.path.join(DEPOSITS, name), encoding="utf-8") as handle:
            rows.extend(entry for entry in json.load(handle)["entries"] if entry.get("resource") in PRECIOUS)
    return rows


class DepositWorkingsTests(unittest.TestCase):
    def test_each_deposit_has_a_working_date_and_size_or_says_it_is_unknown(self):
        bare = [row["id"] for row in precious_deposits()
                if not (row.get("first_worked") is not None and row.get("endowment"))
                and not row.get("working_unknown")]
        self.assertEqual(bare, [])

    def test_a_stated_unknown_gives_no_invented_date_or_size(self):
        invented = [row["id"] for row in precious_deposits()
                    if row.get("working_unknown") and (row.get("first_worked") is not None or row.get("endowment"))]
        self.assertEqual(invented, [])

    def test_a_unknown_working_names_its_confidence_and_what_was_read(self):
        for row in precious_deposits():
            if row.get("working_unknown"):
                self.assertRegex(row["working_unknown"], r"UNKNOWN \([A-D]\)", row["id"])


if __name__ == "__main__":
    unittest.main()
