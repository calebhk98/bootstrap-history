"""The pollution mod keeps each year's concentration and yield factor per tile in tile stores a phase writes (Complaint 639).

`record_pollution` is called with a stand-in for the year's picture; `register` runs against a recording stand-in for the mod API."""
QUICK_TOPIC = True

import unittest

from sim.tests.mod_files import RecordingApi, load_mod_file

MOD = "bh_pollution_t9c3"
HOOKS = load_mod_file(MOD, "hooks.py")


class RecordPollution(unittest.TestCase):
    def setUp(self):
        self.written = {}
        self.original = HOOKS.assess, HOOKS._people_by_tile
        HOOKS.assess = lambda sim: {"tiles": [{"tile": "a", "micrograms_per_cubic_metre": {"particulate": 12.5}, "yield_factor": 0.8}]}
        HOOKS._people_by_tile = lambda sim: {"a": 10.0, "b": 20.0}
        self.addCleanup(lambda: (setattr(HOOKS, "assess", self.original[0]), setattr(HOOKS, "_people_by_tile", self.original[1])))

    def test_an_emitting_tile_gets_its_concentration_and_factor_and_a_clean_settled_tile_gets_clean_values(self):
        HOOKS.record_pollution(None, lambda store, tile, value: self.written.__setitem__((store, tile), value))
        self.assertEqual(self.written[("particulate_micrograms_per_cubic_metre", "a")], 12.5)
        self.assertEqual(self.written[("pollution_yield_factor", "a")], 0.8)
        self.assertEqual(self.written[("particulate_micrograms_per_cubic_metre", "b")], 0.0)
        self.assertEqual(self.written[("pollution_yield_factor", "b")], 1.0)

    def test_register_declares_the_stores_and_a_year_phase_beside_the_externality(self):
        api = RecordingApi(MOD)
        HOOKS.register(api)
        self.assertEqual([call[1][0] for call in api.registered("store")],
                         ["particulate_micrograms_per_cubic_metre", "pollution_yield_factor"])
        (_name, args, fields), = api.registered("phase")
        self.assertEqual((args[:2], fields.get("after")), (("record_pollution", "world"), "market"))
        self.assertEqual(len(api.registered("externality")), 1)


if __name__ == "__main__":
    unittest.main()
