"""`compile_parallel.shares`: every signature lands in exactly one share, the largest kernels are handed out first, and
the work is spread so no share is left far heavier than the rest."""
QUICK_TOPIC = True

import unittest

from sim.ui import compile_parallel


class SharesTest(unittest.TestCase):
    def test_written_out_kernels_go_to_the_lightest_share(self):
        signatures = {"big": [("a",)], "middle": [("b",)], "small": [("c",), ("d",)]}
        sizes = {"big": 100, "middle": 60, "small": 30}
        self.assertEqual(compile_parallel.shares(signatures, sizes, 2),
                         [[("big", ("a",))], [("middle", ("b",)), ("small", ("c",)), ("small", ("d",))]])

    def test_every_signature_once_whatever_the_number_of_jobs(self):
        signatures = {"kernel_%d" % index: [("int64",) * (index % 3 + 1)] for index in range(40)}
        sizes = {name: (index * 37) % 101 for index, name in enumerate(signatures)}
        for jobs in (1, 3, 8):
            pairs = [pair for share in compile_parallel.shares(signatures, sizes, jobs) for pair in share]
            self.assertEqual(sorted(pairs), sorted((name, signature) for name, found in signatures.items() for signature in found))

    def test_a_kernel_of_unknown_size_still_counts_as_work(self):
        shares = compile_parallel.shares({"unknown_a": [("x",)], "unknown_b": [("y",)]}, {}, 2)
        self.assertEqual([len(share) for share in shares], [1, 1])


if __name__ == "__main__":
    unittest.main()
