"""A log line keeps every fact it is given, including one named like its own fields: `log_entry` builds the line an
`unpaid_charge` event records with the refusal's code as its `cause` fact."""

QUICK_TOPIC = True

import pickle
import unittest

from sim.refusal import LogLine, as_record
from sim.reporting.rules import log_entry


class LogLineFactsTest(unittest.TestCase):
    def test_a_fact_named_cause_is_kept_beside_the_kind(self):
        year, line = log_entry(120, "unpaid_charge", "could not pay rent: no cash",
                               {"edge": "suppliers", "amount": 5.0, "cause": "no_cash"})
        self.assertEqual(year, 120)
        self.assertEqual(line.kind, "unpaid_charge")
        self.assertEqual(line.facts, {"edge": "suppliers", "amount": 5.0, "cause": "no_cash"})

    def test_a_line_with_a_cause_fact_survives_a_pickle(self):
        line = LogLine("unpaid_charge", "could not pay rent", None, cause="no_cash")
        copy = pickle.loads(pickle.dumps(line))
        self.assertEqual((copy.kind, copy.facts), ("unpaid_charge", {"cause": "no_cash"}))

    def test_a_cause_fact_reaches_the_saved_record(self):
        record = as_record(LogLine("unpaid_charge", "could not pay rent", None, cause="no_cash"))
        self.assertEqual(record["__log_line__"], "unpaid_charge")
        self.assertEqual(record["facts"]["cause"], "no_cash")


if __name__ == "__main__":
    unittest.main()
