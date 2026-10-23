"""Every command a reply or help text points a player at is a command the parser accepts. `state`'s footer once pointed at
`training_pending` with nothing behind it. The scan reads the source of the packages that write replies for every
`{"cmd":"X"}` and `see 'X'` pointer, so a stale pointer is caught wherever it is printed, without playing a game."""
QUICK_TOPIC = True

import os
import re
import unittest

from sim.ui import protocol

PACKAGES = ("ui", "engine", "agents", "labour", "economy", "geography", "world")
SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_POINTER = re.compile(r'\{\\?"cmd\\?"\s*:\s*\\?"([A-Za-z_]+)')
SEE_POINTER = re.compile(r"see '([A-Za-z_]+)")


def pointers_in_source():
    """{command word: [source files naming it]} for every pointer written in the reply-writing packages."""
    found = {}
    for package in PACKAGES:
        for folder, _names, files in os.walk(os.path.join(SIM_DIR, package)):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as source:
                    text = source.read()
                for word in COMMAND_POINTER.findall(text) + SEE_POINTER.findall(text):
                    found.setdefault(word, []).append(name)
    return found


class CommandPointerTests(unittest.TestCase):
    def test_every_pointer_names_a_command_the_parser_accepts(self):
        accepted = set(protocol.KNOWN_COMMANDS) | set(protocol.TYPED_ALIASES)
        stale = {word: files for word, files in pointers_in_source().items() if word not in accepted}
        self.assertEqual(stale, {})

    def test_the_scan_finds_real_pointers_so_an_empty_result_is_not_a_broken_scan(self):
        self.assertGreaterEqual(len(pointers_in_source()), 10)


if __name__ == "__main__":
    unittest.main()
