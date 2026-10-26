"""SMOKE: protocol golden transcripts. Scripted `agent` sessions (sim/tests/protocol_golden_scripts.py) are replayed
in-process on fixed civilisations and seeds, and every reply, reduced to its structured values (prose becomes a
placeholder; ids, numbers, `cause` and `facts` stay), is compared with the fixture under sim/tests/protocol_golden/.
A failure names the first differing command and key. Re-record with `python3 -m sim.tests.test_protocol_golden --record`
only when a reply is meant to change."""
import json
import os
import sys
import time
import unittest

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sim.tests import protocol_golden_scripts, protocol_golden_support

TOPIC_SECONDS = 240.0
GOLDEN_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protocol_golden")


def fixture_path(script):
    return os.path.join(GOLDEN_DIRECTORY, script["name"] + ".json")


def record(scripts=None):
    os.makedirs(GOLDEN_DIRECTORY, exist_ok=True)
    for script in scripts or protocol_golden_scripts.SCRIPTS:
        started = time.process_time()
        transcript = protocol_golden_support.replay(script)
        with open(fixture_path(script), "w") as handle:
            json.dump({"script": script["name"], "arguments": script["arguments"], "transcript": transcript},
                      handle, indent=1, sort_keys=True)
            handle.write("\n")
        print("recorded %s: %d commands, %.0f cpu seconds" % (script["name"], len(transcript), time.process_time() - started))


class ProtocolGoldenTests(unittest.TestCase):
    def check(self, script):
        with open(fixture_path(script)) as handle:
            expected = json.load(handle)["transcript"]
        actual = protocol_golden_support.replay(script)
        difference = protocol_golden_support.compare(expected, json.loads(json.dumps(actual)))
        self.assertIsNone(difference, "%s: %s" % (script["name"], difference))

    def test_rome_founder(self):
        self.check(protocol_golden_scripts.FOUNDER)

    def test_han_two_seats_fog(self):
        self.check(protocol_golden_scripts.SECOND_SEAT)

    def test_norse_session_round_trips(self):
        self.check(protocol_golden_scripts.SESSION)


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
    else:
        unittest.main()
