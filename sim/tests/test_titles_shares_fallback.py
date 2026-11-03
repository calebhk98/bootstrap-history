"""`titles.shares` reads the record's titles; it falls back on the cohorts' ownership shares only for a record with no
titles at all yet, never for a tile whose holders have all let go of it."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import titles


def record_with(titles_by_tile):
    cohort = types.SimpleNamespace(agent_id="c", tile="t", ownership_share=1.0)
    return types.SimpleNamespace(land=types.SimpleNamespace(titles=titles_by_tile), cohorts={"c": cohort})


class SharesFallbackTests(unittest.TestCase):
    def test_a_record_with_no_titles_yet_reads_the_ownership_shares(self):
        self.assertEqual(titles.shares(record_with({}), "t"), {"c": 1.0})

    def test_a_tile_whose_holders_all_released_it_has_no_holder(self):
        self.assertEqual(titles.shares(record_with({"t": {}, "u": {"x": 1.0}}), "t"), {})

    def test_a_tile_the_titles_do_not_name_has_no_holder_once_titles_exist(self):
        self.assertEqual(titles.shares(record_with({"u": {"x": 1.0}}), "t"), {})

    def test_held_titles_are_returned_as_they_are(self):
        self.assertEqual(titles.shares(record_with({"t": {"x": 0.4}}), "t"), {"x": 0.4})


if __name__ == "__main__":
    unittest.main()
