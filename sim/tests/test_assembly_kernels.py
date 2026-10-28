"""Kernels on an assembly: a module declares them, a mod replaces one, and the replacement must answer the kernel's samples."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import AssemblyError, Kernel, Operations, record
from sim.assembly.kernels import same
from sim.engine import game_assembly
from sim.tests.assembly_fixture import BASE, TOP, build, changed


def total(values, scale=1.0):
    return sum(values) * scale


def total_samples():
    return [(([1.0, 2.0, 3.0],), {}), (([0.5, 0.25],), {"scale": 2.0})]


KERNEL = Kernel("base.total", total, inputs="numbers and a scale", output="their scaled sum", samples=total_samples)
OWNER = changed(BASE, kernels=(KERNEL,))


def reversed_sum(values, scale=1.0):
    return sum(reversed(values)) * scale


def off_by_one(values, scale=1.0):
    return sum(values) * scale + 1.0


def nearly(values, scale=1.0):
    return total(values, scale) * (1.0 + 1e-6)


def assemble_with(*mods):
    return build(shipped=(OWNER, TOP), operations=[Operations(mod_id, kernels={"base.total": function}) for mod_id, function in mods])


class KernelDeclarationTest(unittest.TestCase):
    def test_without_a_mod_the_module_is_handed_the_reference(self):
        assembly = assemble_with()
        self.assertIs(assembly.kernels["base.total"], total)
        self.assertIs(assembly.modules["base"].kernel("base.total"), total)
        self.assertEqual(assembly.kernel_owner, {"base.total": "base"})

    def test_a_kernel_must_be_named_for_its_module(self):
        stray = changed(BASE, kernels=(Kernel("other.total", total, "", "", total_samples),))
        with self.assertRaises(AssemblyError) as caught:
            build(shipped=(stray, TOP))
        self.assertIn("other.total", str(caught.exception))   # presentation: the error names the kernel

    def test_a_tolerance_needs_its_reason(self):
        with self.assertRaises(AssemblyError):
            Kernel("base.total", total, "", "", total_samples, tolerance=1e-9)
        self.assertEqual(Kernel("base.total", total, "", "", total_samples, tolerance=1e-9, tolerance_reason="float sum order").tolerance, 1e-9)


class KernelReplacementTest(unittest.TestCase):
    def test_an_equal_replacement_is_bound_and_recorded(self):
        assembly = assemble_with(("fast", reversed_sum))
        self.assertIs(assembly.modules["base"].kernel("base.total"), reversed_sum)
        self.assertEqual(record(assembly)["kernels"], {"base.total": "fast"})

    def test_the_record_of_a_game_without_a_replacement_has_none(self):
        self.assertEqual(record(assemble_with())["kernels"], {})

    def test_a_wrong_replacement_is_refused_naming_the_mod_and_the_kernel(self):
        with self.assertRaises(AssemblyError) as caught:
            assemble_with(("slow_and_wrong", off_by_one))
        self.assertIn("slow_and_wrong", str(caught.exception))   # presentation: the error names the mod and the kernel
        self.assertIn("base.total", str(caught.exception))

    def test_a_replacement_that_raises_is_refused_naming_the_mod_and_the_kernel(self):
        def broken(values, scale=1.0):
            raise RuntimeError("no")
        with self.assertRaises(AssemblyError) as caught:
            assemble_with(("brittle", broken))
        self.assertIn("brittle", str(caught.exception))   # presentation: the error names the mod and the kernel
        self.assertIn("base.total", str(caught.exception))

    def test_a_replacement_of_a_kernel_no_module_declares_is_refused(self):
        with self.assertRaises(AssemblyError) as caught:
            build(operations=[Operations("fast", kernels={"base.total": total})])
        self.assertIn("fast", str(caught.exception))   # presentation: the error names the mod and the kernel
        self.assertIn("base.total", str(caught.exception))

    def test_two_mods_replacing_one_kernel_are_refused_naming_both(self):
        with self.assertRaises(AssemblyError) as caught:
            assemble_with(("first", reversed_sum), ("second", reversed_sum))
        self.assertIn("first", str(caught.exception))   # presentation: the error names both mods and the kernel
        self.assertIn("second", str(caught.exception))
        self.assertIn("base.total", str(caught.exception))

    def test_a_difference_inside_the_declared_tolerance_is_accepted(self):
        loose = changed(BASE, kernels=(Kernel("base.total", total, "", "", total_samples, tolerance=1e-3,
                                              tolerance_reason="a float sum in another order"),))
        assembly = build(shipped=(loose, TOP), operations=[Operations("fast", kernels={"base.total": nearly})])
        self.assertIs(assembly.kernels["base.total"], nearly)

    def test_an_exact_kernel_refuses_the_same_small_difference(self):
        with self.assertRaises(AssemblyError):
            assemble_with(("fast", nearly))

    def test_only_the_observed_part_of_an_answer_is_compared(self):
        def pairs(first, second):
            return (first + second, "scratch")
        kernel = Kernel("base.pairs", pairs, "", "", lambda: [((1.0, 2.0), {})], observe=lambda arguments, keywords, answer: answer[0])
        spec = changed(BASE, kernels=(kernel,))
        assembly = build(shipped=(spec, TOP), operations=[Operations("fast", kernels={"base.pairs": lambda first, second: (second + first, "other")})])
        self.assertEqual(record(assembly)["kernels"], {"base.pairs": "fast"})


class SameTest(unittest.TestCase):
    def test_floats_ints_and_containers(self):
        self.assertTrue(same([1.0, {"a": (2.0, None)}], [1.0, {"a": (2.0, None)}], 0.0))
        self.assertFalse(same(1.0, 1.0 + 1e-15, 0.0))
        self.assertTrue(same(1.0, 1.0 + 1e-15, 1e-12))
        self.assertFalse(same([1.0], [1.0, 2.0], 0.0))
        self.assertFalse(same({"a": 1.0, "b": 2.0}, {"b": 2.0, "a": 1.0}, 0.0))   # keys in the reference's order
        self.assertFalse(same(None, 0.0, 0.0))
        self.assertTrue(same(float("nan"), float("nan"), 0.0))

    def test_a_tolerance_has_a_floor_near_zero(self):
        self.assertTrue(same(0.0, 1e-13, 1e-12))
        self.assertFalse(same(0.0, 1e-9, 1e-12))


class SaveRefusalTest(unittest.TestCase):
    def test_a_save_from_a_game_with_a_replaced_kernel_is_refused_by_one_without(self):
        replaced = assemble_with(("fast", reversed_sum))
        plain = assemble_with()
        reason = game_assembly.check_record(plain, record(replaced))
        self.assertIsNotNone(reason)
        self.assertIn("base.total", reason)   # presentation: the refusal names the kernel
        self.assertIsNotNone(game_assembly.check_record(replaced, record(plain)))

    def test_the_same_kernel_replacements_agree(self):
        self.assertIsNone(game_assembly.check_record(assemble_with(("fast", reversed_sum)), record(assemble_with(("fast", reversed_sum)))))


if __name__ == "__main__":
    unittest.main()
