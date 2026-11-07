"""`sim.jit.njit` compiles a kernel when numba is present and returns the plain function otherwise; either way the kernel
gives the same answer."""
QUICK_TOPIC = True

import importlib
import os
import unittest
from unittest import mock

import numpy

from sim import jit


def _total(values):
    total = 0.0
    for index in range(values.shape[0]):
        total += values[index]
    return total


class JitTests(unittest.TestCase):
    def test_a_kernel_gives_the_plain_functions_answer(self):
        values = numpy.arange(10.0)
        self.assertEqual(jit.njit(_total)(values), _total(values))

    def test_without_numba_the_function_is_returned_unchanged(self):
        # the variable is put back as it was (a run with ROME_NO_JIT set must stay without numba after this test)
        try:
            with mock.patch.dict(os.environ, {jit.NO_JIT_ENV: "1"}):
                plain = importlib.reload(jit)
                self.assertFalse(plain.ENABLED)
                self.assertIs(plain.njit(_total), _total)
        finally:
            importlib.reload(jit)


if __name__ == "__main__":
    unittest.main()
