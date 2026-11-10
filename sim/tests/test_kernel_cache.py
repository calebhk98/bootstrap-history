"""The compiled-kernel cache directory follows the content of every file that defines a kernel, so a callee edited in
another file is never served from a caller compiled against its old code."""

QUICK_TOPIC = True

import os
import tempfile
import time
import unittest
from unittest import mock

from sim.kernel_cache import SCOPE_ENV, kernel_files, kernel_source_key, prune, scope


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class KernelSourceKeyTests(unittest.TestCase):
    def setUp(self):
        self.top = tempfile.mkdtemp()
        write(os.path.join(self.top, "caller.py"), "from .callee import helper\n@njit\ndef caller(x):\n    return helper(x)\n")
        write(os.path.join(self.top, "callee.py"), "@njit\ndef helper(x):\n    return x + 1\n")
        write(os.path.join(self.top, "plain.py"), "def not_a_kernel():\n    return 1\n")
        write(os.path.join(self.top, "tests", "test_x.py"), "@njit\ndef in_a_test():\n    return 1\n")

    def test_only_kernel_files_outside_tests_are_hashed(self):
        self.assertEqual([os.path.basename(path) for path in kernel_files(self.top)], ["callee.py", "caller.py"])

    def test_editing_a_callee_in_another_file_changes_the_key(self):
        before = kernel_source_key(self.top)
        write(os.path.join(self.top, "callee.py"), "@njit\ndef helper(x):\n    return x + 2\n")
        self.assertNotEqual(kernel_source_key(self.top), before)

    def test_editing_a_file_without_kernels_keeps_the_kernels_key(self):
        before = kernel_source_key(self.top, "kernels")
        write(os.path.join(self.top, "plain.py"), "def not_a_kernel():\n    return 2\n")
        self.assertEqual(kernel_source_key(self.top, "kernels"), before)

    def test_editing_a_file_without_kernels_changes_the_source_key(self):
        before = kernel_source_key(self.top, "source")
        write(os.path.join(self.top, "plain.py"), "LIMIT = 2\n")
        self.assertNotEqual(kernel_source_key(self.top, "source"), before)

    def test_the_source_scope_covers_every_file_but_the_tests(self):
        self.assertEqual([os.path.basename(path) for path in kernel_files(self.top, "source")], ["callee.py", "caller.py", "plain.py"])


class ScopeTests(unittest.TestCase):
    def test_unset_means_the_whole_source_and_an_unknown_value_refuses(self):
        with mock.patch.dict(os.environ, {SCOPE_ENV: ""}):
            self.assertEqual(scope(), "source")
        with mock.patch.dict(os.environ, {SCOPE_ENV: "kernels"}):
            self.assertEqual(scope(), "kernels")
        with mock.patch.dict(os.environ, {SCOPE_ENV: "everything"}):
            with self.assertRaises(ValueError):
                scope()


class PruneTests(unittest.TestCase):
    def test_keeps_the_current_and_the_most_recent_others(self):
        parent = tempfile.mkdtemp()
        names = ["a", "b", "c", "d", "e"]
        for age, name in enumerate(names):
            os.makedirs(os.path.join(parent, name))
            stamp = time.time() - 100 + age
            os.utime(os.path.join(parent, name), (stamp, stamp))
        prune(parent, os.path.join(parent, "a"), kept=3)
        self.assertEqual(sorted(os.listdir(parent)), ["a", "d", "e"])


if __name__ == "__main__":
    unittest.main()
