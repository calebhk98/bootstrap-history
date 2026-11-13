"""SMOKE: `compile-kernels` leaves every registered kernel with a compiled signature (a cold cache takes minutes), so a new
kernel that neither the fixture economy nor `kernel_signatures.py` reaches fails here, and the command's setup-script
use stays complete."""

CIVILISATIONS = ()   # builds no game, so the runner warms no start for it
import unittest

from sim import jit
from sim.ui import cli_compile_kernels


@unittest.skipUnless(jit.ENABLED, "numba is not in use")
class CompileKernelsTests(unittest.TestCase):
    def test_every_registered_kernel_is_compiled(self):
        _seconds, missing = cli_compile_kernels.compile_all()
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
