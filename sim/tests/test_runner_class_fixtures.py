"""The runner runs a unittest topic one class at a time: setUpClass once for the class, each test still its own
check, a class fixture that fails failing every test of its class, and a failing subtest failing its test."""

QUICK_TOPIC = True

import sys
import types
import unittest

from sim.tests import __main__ as runner

PROBE = "runner_fixture_probe"


class _Recorder:
    def __init__(self):
        self.checks, self._LAST_AT = [], 0.0

    def check(self, name, passed, detail=""):
        self.checks.append((name.split(": ", 1)[1], passed))


def _run_probe_module(classes):
    module = types.ModuleType("sim.tests.test_" + PROBE)
    for test_class in classes:
        test_class.__module__ = module.__name__
        setattr(module, test_class.__name__, test_class)
    sys.modules[module.__name__] = module
    try:
        recorder = _Recorder()
        runner._run_topic(PROBE, recorder)
        return recorder.checks
    finally:
        del sys.modules[module.__name__]


class RunnerClassFixtureTests(unittest.TestCase):
    def test_set_up_class_runs_once_and_every_test_is_a_check(self):
        built = []

        class Shared(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                built.append(1)

            def test_one(self):
                pass

            def test_two(self):
                self.assertEqual(1, 2)

        checks = _run_probe_module([Shared])
        self.assertEqual(len(built), 1)
        self.assertEqual(checks, [("test one", True), ("test two", False)])

    def test_a_failing_class_fixture_fails_each_of_its_tests(self):
        class Broken(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("no game")

            def test_one(self):
                pass

            def test_two(self):
                pass

        self.assertEqual(_run_probe_module([Broken]), [("test one", False), ("test two", False)])

    def test_a_failing_subtest_fails_its_test(self):
        class WithSubtests(unittest.TestCase):
            def test_cases(self):
                for value in (1, 2):
                    with self.subTest(value=value):
                        self.assertEqual(value, 1)

        self.assertEqual(_run_probe_module([WithSubtests]), [("test cases", False)])
