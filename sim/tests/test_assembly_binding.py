"""Assembly binding: every read has one provider, every command one owner, and the errors name the parties."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import AssemblyError, Module, ModuleSpec, PhaseHook, ViewSpec
from sim.tests.assembly_fixture import BASE, TOP, SetValue, Unapplied, build, changed


class Plain:
    """Not a Module."""


class Twin(Module):
    def other_raw(self):
        return 0


class BindingTest(unittest.TestCase):
    def test_a_read_with_no_provider_names_reader_and_view(self):
        with self.assertRaises(AssemblyError) as caught:
            build(shipped=[TOP])
        self.assertIn("top", str(caught.exception))  # presentation: the error text is the only carrier of the parties
        self.assertIn("double", str(caught.exception))

    def test_two_publishers_of_a_view_name_both(self):
        twin = ModuleSpec("twin", Twin, publishes=(ViewSpec("raw", "other_raw"),))
        with self.assertRaises(AssemblyError) as caught:
            build(twin)
        self.assertIn("base", str(caught.exception))  # presentation: names both modules
        self.assertIn("twin", str(caught.exception))

    def test_two_appliers_of_a_command_name_both(self):
        twin = ModuleSpec("twin", Twin, applies=((SetValue, "other_raw"),))
        with self.assertRaises(AssemblyError) as caught:
            build(twin)
        self.assertIn("base", str(caught.exception))  # presentation: names both modules
        self.assertIn("twin", str(caught.exception))

    def test_a_view_input_not_in_reads_is_refused(self):
        bad = changed(TOP, reads=())
        with self.assertRaises(AssemblyError):
            build(shipped=[BASE, bad])

    def test_sending_a_command_nobody_applies_is_refused(self):
        sender = ModuleSpec("sender", Twin, sends=(Unapplied,))
        with self.assertRaises(AssemblyError):
            build(sender)

    def test_optional_read_absent_is_none_on_needs(self):
        reader = ModuleSpec("reader", Twin, optional_reads=("nothing_provides_this",))
        assembly = build(reader)
        self.assertIsNone(assembly.modules["reader"].needs.nothing_provides_this)

    def test_optional_read_present_is_the_view(self):
        reader = ModuleSpec("reader", Twin, optional_reads=("raw",))
        assembly = build(reader)
        self.assertIs(assembly.modules["reader"].needs.raw, assembly.views["raw"])

    def test_an_undeclared_view_is_not_on_needs(self):
        assembly = build()
        with self.assertRaises(AttributeError):
            assembly.modules["top"].needs.raw

    def test_an_implementation_not_deriving_module_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(ModuleSpec("odd", Plain))

    def test_a_declared_method_that_is_missing_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(ModuleSpec("odd", Twin, publishes=(ViewSpec("ghost", "no_such_method"),)))

    def test_a_declared_phase_method_that_is_missing_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(ModuleSpec("odd", Twin, phases=(PhaseHook("market", "no_such_method"),)))

    def test_phase_handlers_maps_phase_names_to_methods(self):
        hooked = changed(BASE, phases=(PhaseHook("market", "run_market"),))
        handlers = build(shipped=[hooked, TOP]).phase_handlers()
        self.assertEqual(handlers["market"](), "market")

    def test_two_modules_on_one_phase_are_refused(self):
        hooked = changed(BASE, phases=(PhaseHook("market", "run_market"),))
        rival = ModuleSpec("rival", Twin, phases=(PhaseHook("market", "other_raw"),))
        assembly = build(rival, shipped=[hooked, TOP])
        with self.assertRaises(AssemblyError):
            assembly.phase_handlers()

    def test_two_shipped_modules_with_one_id_are_refused(self):
        with self.assertRaises(AssemblyError):
            build(BASE)

    def test_a_module_gets_its_id_and_the_shared_clock(self):
        assembly = build()
        self.assertEqual(assembly.modules["base"].module_id, "base")
        self.assertIs(assembly.modules["base"].clock, assembly.clock)

    def test_setup_runs_once_after_assembly(self):
        self.assertEqual(build().modules["base"].value, 1)


if __name__ == "__main__":
    unittest.main()
