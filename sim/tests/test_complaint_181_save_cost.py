"""Complaint 181: a command that changes nothing must not pay for rewriting the whole save, and writing a save must not
go through the slow pure-Python JSON encoder. Counted work, not clock time. The rules are `save_state`'s skip of an
unchanged game and `state_json` (sim/engine/saveload.py), and the scan's reads of the society's baseline knowledge
(sim/agents/base.py), each called on inputs built here. (The play loop asking the save policy once per command: test_play_run_one_command.)"""
QUICK_TOPIC = True

import json.encoder as json_encoder
import os
import tempfile
import unittest
from unittest import mock

from sim.agents.api import ActorRecord, Firm
from sim.engine import saveload
from sim.tests.agents_fake_world import FakeWorld, make_node


class CountWrites:
    """Counts how many times a save replaced the file, and how many times the pure-Python JSON encoder was built."""

    def __enter__(self):
        self.replaces = 0
        self.python_encoder_builds = 0
        self._real_replace = os.replace
        self._real_make_iterencode = json_encoder._make_iterencode

        def counting_replace(source, destination):
            self.replaces += 1
            return self._real_replace(source, destination)

        def counting_make_iterencode(*arguments, **keywords):
            self.python_encoder_builds += 1
            return self._real_make_iterencode(*arguments, **keywords)

        os.replace = counting_replace
        json_encoder._make_iterencode = counting_make_iterencode
        return self

    def __exit__(self, *exception):
        os.replace = self._real_replace
        json_encoder._make_iterencode = self._real_make_iterencode


class SaveSkipTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "session.json")
        self.text = ['{"year":100}']
        patcher = mock.patch.object(saveload, "state_text", lambda game: self.text[0])
        patcher.start()
        self.addCleanup(patcher.stop)

    def save(self):
        with CountWrites() as counted:
            saveload.save_state(object(), self.path)
        return counted.replaces

    def test_the_first_save_writes_the_file(self):
        self.assertEqual(self.save(), 1)
        with open(self.path) as handle:
            self.assertEqual(handle.read(), '{"year":100}')

    def test_a_game_that_changed_nothing_rewrites_the_save_zero_times(self):
        self.save()
        self.assertEqual([self.save() for _ in range(3)], [0, 0, 0])

    def test_a_game_that_changed_rewrites_it_once_and_the_file_is_the_new_game(self):
        self.save()
        self.text[0] = '{"year":101}'
        self.assertEqual(self.save(), 1)
        with open(self.path) as handle:
            self.assertEqual(handle.read(), '{"year":101}')

    def test_a_file_changed_behind_the_games_back_is_rewritten(self):
        self.save()
        with open(self.path, "w") as handle:
            handle.write("something else")
        self.assertEqual(self.save(), 1)
        with open(self.path) as handle:
            self.assertEqual(handle.read(), '{"year":100}')

    def test_a_gz_path_is_compressed_and_read_back(self):
        self.path += ".gz"
        self.save()
        self.assertEqual(saveload.read_save_text(self.path), '{"year":100}')


class StateJsonTests(unittest.TestCase):
    SERIALIZED = {"seats": [{"capital": 1.5, "done": ["a", "b"], "notes": {"x": None}}] * 50, "when": {"year": 100}}

    def test_a_save_is_encoded_without_the_pure_python_json_encoder(self):
        with CountWrites() as counted:
            saveload.state_json(self.SERIALIZED)
        self.assertEqual(counted.python_encoder_builds, 0)

    def test_a_save_is_compact_one_line_without_indentation(self):
        text = saveload.state_json(self.SERIALIZED)
        self.assertLess(len(text.splitlines()), 50)
        self.assertNotIn("\n", text)
        self.assertNotIn(", ", text)

    def test_what_is_encoded_reads_back_the_same(self):
        import json
        self.assertEqual(json.loads(saveload.state_json(self.SERIALIZED)), self.SERIALIZED)

    def test_a_value_json_cannot_encode_is_written_as_text_not_refused(self):
        self.assertIn("{1, 2}", saveload.state_json({"set": {1, 2}}).replace("'", ""))


class ImitationScanTests(unittest.TestCase):
    """The society's baseline knowledge is read a constant number of times per scan, not once per invention."""

    class CountingWorld(FakeWorld):
        def __init__(self, inventions):
            super().__init__()
            self.baseline_reads = 0
            for number in range(inventions):
                node_id = "invention_%03d" % number
                self.nodes[node_id] = make_node(node_id, revenue=50.0)
                self.demonstrated_nodes.add(node_id)

        def baseline_knowledge(self):
            self.baseline_reads += 1
            return self.baseline

    def reads(self, inventions):
        world = self.CountingWorld(inventions)
        firm = Firm("firm:scan", ActorRecord(kind="firm", money=1e6))
        firm.imitation_options(world)
        return world.baseline_reads, len(world.founder_inventions())

    def test_the_scan_has_many_inventions_to_look_at(self):
        self.assertGreaterEqual(self.reads(80)[1], 50)

    def test_the_baseline_knowledge_is_read_a_constant_number_of_times_per_scan(self):
        few, _ = self.reads(10)
        many, scanned = self.reads(80)
        self.assertTrue(1 <= many <= 5, (many, scanned))
        self.assertEqual(few, many)


if __name__ == "__main__":
    unittest.main()
