"""`cold_compile`: a cache directory is cold until it holds a compiled kernel's index, and the switch turns it off."""
QUICK_TOPIC = True

import os
import tempfile
import unittest
from unittest import mock

from sim.ui import cold_compile


class CacheHoldsKernelsTest(unittest.TestCase):
    def test_an_empty_or_unrelated_directory_is_cold(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(cold_compile.cache_holds_kernels(directory))
            open(os.path.join(directory, "notes.txt"), "w").close()
            self.assertFalse(cold_compile.cache_holds_kernels(directory))

    def test_an_index_anywhere_below_makes_it_warm(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "sim", "economy"))
            open(os.path.join(directory, "sim", "economy", "plan_kernel.plan_rows-23.py313.nbi"), "w").close()
            self.assertTrue(cold_compile.cache_holds_kernels(directory))


class SwitchTest(unittest.TestCase):
    def test_the_switch_off_compiles_nothing(self):
        with mock.patch.dict(os.environ, {cold_compile.SWITCH_ENV: "0"}), \
                mock.patch.object(cold_compile.compile_parallel, "compile_in_parallel") as compile_in_parallel:
            self.assertFalse(cold_compile.compile_if_cold())
        compile_in_parallel.assert_not_called()

    def test_a_cold_cache_with_cores_compiles(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"NUMBA_CACHE_DIR": directory}), \
                mock.patch.object(cold_compile, "jobs_of", return_value=4), \
                mock.patch.object(cold_compile.jit, "ENABLED", True), \
                mock.patch.object(cold_compile.compile_parallel, "compile_in_parallel") as compile_in_parallel:
            os.environ.pop(cold_compile.SWITCH_ENV, None)
            self.assertTrue(cold_compile.compile_if_cold())
        compile_in_parallel.assert_called_once_with(4)


if __name__ == "__main__":
    unittest.main()
