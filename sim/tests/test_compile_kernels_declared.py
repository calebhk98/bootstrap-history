"""`kernel_signatures.declared_signatures`: every entry names a registered kernel and gives one type per argument, so
`compile-kernels` can compile it from types. No game is built (importing the kernel modules fills `jit.REGISTRY`)."""
QUICK_TOPIC = True

import inspect
import unittest

from sim import jit
from sim.ui import cli_compile_kernels
from sim.ui.kernel_signatures import declared_signatures


@unittest.skipUnless(jit.ENABLED, "numba is not in use")
class DeclaredSignatureTests(unittest.TestCase):
    def test_each_entry_names_a_kernel_and_types_every_argument(self):
        cli_compile_kernels.import_kernel_modules()
        kernels = {cli_compile_kernels.kernel_name(kernel): kernel for kernel in jit.REGISTRY}
        for name, signatures in declared_signatures().items():
            self.assertIn(name, kernels)
            arguments = len(inspect.signature(kernels[name].py_func).parameters)
            for argument_types in signatures:
                self.assertEqual(len(argument_types), arguments, name)


if __name__ == "__main__":
    unittest.main()
