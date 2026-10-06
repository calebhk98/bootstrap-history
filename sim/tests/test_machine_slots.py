"""Suite workers draw on one machine-wide pool of slots, so suites run at once share the cores.

sim/tests/machine_slots.py."""
QUICK_TOPIC = True

import os
import subprocess
import sys
import tempfile
import unittest

from sim.tests import machine_slots


@unittest.skipIf(machine_slots.fcntl is None, "no file locks on this platform")
class SlotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="suite_slots_")

    def test_no_more_slots_than_the_pool_holds(self):
        first = machine_slots.acquire(2, self.directory)
        second = machine_slots.acquire(2, self.directory)
        self.assertTrue(first and second)
        self.assertIs(machine_slots.acquire(2, self.directory, wait=False), False)
        machine_slots.release(first)
        third = machine_slots.acquire(2, self.directory, wait=False)
        self.assertTrue(third)
        machine_slots.release(second)
        machine_slots.release(third)

    def test_another_process_holding_a_slot_counts_against_the_pool(self):
        script = ("import sys; sys.path.insert(0, %r)\n"
                  "from sim.tests import machine_slots\n"
                  "handle = machine_slots.acquire(1, %r)\n"
                  "print('held', flush=True); sys.stdin.readline()\n"
                  % (os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     self.directory))
        holder = subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(holder.stdout.readline().strip(), "held")
            self.assertIs(machine_slots.acquire(1, self.directory, wait=False), False)
        finally:
            holder.communicate("\n")
        freed = machine_slots.acquire(1, self.directory, wait=False)
        self.assertTrue(freed, "a slot is freed when the process holding it exits")
        machine_slots.release(freed)


if __name__ == "__main__":
    unittest.main()
