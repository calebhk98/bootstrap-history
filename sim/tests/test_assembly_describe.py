"""The assembly's description: the record a save keeps, and the dependency listing."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import ExtensionPoint, Module, ModuleSpec, Operations, ViewSpec, dependency_lines, record
from sim.tests.assembly_fixture import BASE, Base, SetValue, build, changed


class Quiet(Module):
    def provided(self):
        return 5


class Replacement(Base):
    pass


class Layer:
    def double(self):
        return super().double()


class Helping:
    def helper(self):
        return 1


def dotted(klass):
    return "%s.%s" % (klass.__module__, klass.__qualname__)


def full_assembly():
    town = ModuleSpec("town", Quiet, extension_points=(ExtensionPoint("town_size"),))
    gone = ModuleSpec("gone", Quiet)
    added = ModuleSpec("one:extra", Quiet, publishes=(ViewSpec("extra", "provided"),))
    operations = [
        Operations("one", added=(added,), replaced={"base": changed(BASE, implementation=Replacement)}),
        Operations("two", layers={"top": (Layer,)}, adjusters={"double": ((lambda needs, value: value, ()),)},
                   provided={"town_size": (lambda: 1,)}),
        Operations("three", removed=("gone",))]
    return build(town, gone, operations=operations)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.record = record(full_assembly())

    def test_origin_is_shipped_or_the_adding_mod(self):
        modules = self.record["modules"]
        self.assertEqual(modules["base"]["origin"], "shipped")
        self.assertEqual(modules["one:extra"]["origin"], "one")

    def test_replaced_by_names_the_mod_and_the_new_implementation(self):
        entry = self.record["modules"]["base"]
        self.assertEqual(entry["replaced_by"], "one")
        self.assertEqual(entry["implementation"], dotted(Replacement))
        self.assertIsNone(self.record["modules"]["top"]["replaced_by"])

    def test_layers_list_mod_and_class_in_order(self):
        self.assertEqual(self.record["modules"]["top"]["layers"], [["two", dotted(Layer)]])
        self.assertEqual(self.record["modules"]["base"]["layers"], [])

    def test_removed_modules_are_listed_with_their_remover_and_not_as_modules(self):
        self.assertEqual(self.record["removed"], {"gone": "three"})
        self.assertNotIn("gone", self.record["modules"])

    def test_adjusters_list_mods_per_view(self):
        self.assertEqual(self.record["adjusters"], {"double": ["two"]})

    def test_provided_lists_mods_per_point(self):
        self.assertEqual(self.record["provided"], {"town_size": ["two"]})

    def test_equal_assemblies_have_equal_records(self):
        self.assertEqual(record(full_assembly()), record(full_assembly()))

    def test_a_different_mod_set_has_a_different_record(self):
        self.assertNotEqual(record(full_assembly()), record(build()))


class DependencyLinesTest(unittest.TestCase):
    def test_every_module_gets_a_block_with_its_reads_and_providers(self):
        lines = dependency_lines(build())
        self.assertIn("top", lines)
        self.assertIn("  reads: double (base)", lines)  # presentation: the listing's layout

    def test_sends_name_the_owner(self):
        caller = ModuleSpec("caller", Quiet, sends=(SetValue,))
        lines = dependency_lines(build(caller))
        self.assertIn("  sends: SetValue (base)", lines)  # presentation: the listing's layout

    def test_an_absent_optional_read_is_listed_absent(self):
        reader = ModuleSpec("reader", Quiet, optional_reads=("nowhere",))
        self.assertIn("  reads if present: nowhere (absent)", dependency_lines(build(reader)))  # presentation: layout

    def test_a_layer_overriding_an_undeclared_method_is_listed(self):
        assembly = build(operations=[Operations("one", layers={"base": (Helping,)})])
        listed = [line for line in dependency_lines(assembly) if "unstable" in line]  # presentation: the listing's marker
        self.assertEqual(len(listed), 1)
        self.assertIn("helper", listed[0])
        self.assertIn("one", listed[0])

    def test_a_layer_overriding_a_declared_method_is_not_listed(self):
        assembly = build(operations=[Operations("one", layers={"base": (Layer,)})])
        self.assertEqual([line for line in dependency_lines(assembly) if "unstable" in line], [])  # presentation: marker


if __name__ == "__main__":
    unittest.main()
