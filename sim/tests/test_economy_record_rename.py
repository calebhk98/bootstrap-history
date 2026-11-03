"""A renamed agent leaves nothing behind under its old id in the land and labour parts of the economy record. Each part's
`rename_agent` is called on a part written out here."""
QUICK_TOPIC = True

import unittest

from sim.economy.labour_record import LabourRecord
from sim.economy.land_record import LandRecord


class LandRename(unittest.TestCase):
    def test_a_tenancy_names_the_new_tenant_and_lessor(self):
        land = LandRecord(titles={"t1": {"old": 0.5, "other": 0.5}},
                          tenancies={"t1": [{"tenant": "old", "lessor": "other", "share": 0.2, "arrears": 0.0},
                                            {"tenant": "other", "lessor": "old", "share": 0.1, "arrears": 1.0}]})
        land.rename_agent("old", "new")
        self.assertEqual(set(land.titles["t1"]), {"new", "other"})
        self.assertEqual([(row["tenant"], row["lessor"]) for row in land.tenancies["t1"]],
                         [("new", "other"), ("other", "new")])


class LabourRename(unittest.TestCase):
    def test_an_employer_in_the_cores_hired_hours_is_renamed(self):
        labour = LabourRecord()
        labour.workforce.hired_hours = {"north": {"smith": {"old": 10.0, "other": 5.0}}}
        labour.hours_paid_by_employer = {"old": {"smith": 10.0}}
        labour.rename_agent("old", "new")
        self.assertEqual(labour.workforce.hired_hours, {"north": {"smith": {"new": 10.0, "other": 5.0}}})
        self.assertEqual(labour.hours_paid_by_employer, {"new": {"smith": 10.0}})


if __name__ == "__main__":
    unittest.main()
