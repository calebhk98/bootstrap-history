"""Assembly commands and extension points: send is checked against `sends`, points combine in provider order."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import FIRST, LIST, SUM, AssemblyError, ExtensionPoint, Module, ModuleSpec, Operations, Point, Provision, assemble
from sim.tests.assembly_fixture import BASE, TOP, SetValue, build, changed


class Caller(Module):
    pass


def point_with(combine, *providers):
    point = Point("toy_point", combine)
    point.providers.extend(providers)
    return point


class SendTest(unittest.TestCase):
    def test_send_applies_through_the_owner_and_returns_its_result(self):
        assembly = build(ModuleSpec("caller", Caller, sends=(SetValue,)))
        self.assertEqual(assembly.modules["caller"].needs.send(SetValue(7)), 7)
        self.assertEqual(assembly.modules["base"].value, 7)

    def test_send_bumps_through_the_owner_so_views_refresh(self):
        assembly = build(ModuleSpec("caller", Caller, sends=(SetValue,)))
        self.assertEqual(assembly.views["double"](), 2)
        assembly.modules["caller"].needs.send(SetValue(7))
        self.assertEqual(assembly.views["double"](), 14)

    def test_send_refuses_an_undeclared_command_type(self):
        assembly = build(ModuleSpec("caller", Caller))
        with self.assertRaises(AssemblyError):
            assembly.modules["caller"].needs.send(SetValue(7))
        self.assertEqual(assembly.modules["base"].value, 1)


class PointCombineTest(unittest.TestCase):
    def test_sum_adds_answers(self):
        self.assertEqual(point_with(SUM, lambda x: x, lambda x: 10 * x)(2), 22)

    def test_sum_with_no_provider_is_zero(self):
        self.assertEqual(point_with(SUM)(2), 0)

    def test_first_takes_the_first_answer_that_is_not_none_in_provider_order(self):
        self.assertEqual(point_with(FIRST, lambda: None, lambda: 0, lambda: 5)(), 0)

    def test_first_with_only_none_is_none(self):
        self.assertIsNone(point_with(FIRST, lambda: None)())

    def test_first_stops_asking_after_an_answer(self):
        asked = []
        point_with(FIRST, lambda: 1, lambda: asked.append("second"))()
        self.assertEqual(asked, [])

    def test_list_keeps_provider_order(self):
        self.assertEqual(point_with(LIST, lambda: "a", lambda: "b", lambda: "c")(), ["a", "b", "c"])

    def test_an_unknown_rule_is_an_assembly_error(self):
        with self.assertRaises(AssemblyError):
            point_with("median", lambda: 1)()


class PointAssemblyTest(unittest.TestCase):
    def town(self):
        return ModuleSpec("town", Caller, extension_points=(ExtensionPoint("town_size", LIST),))

    def test_providers_answer_in_mod_load_order(self):
        first = Operations("one", provided={"town_size": (lambda name: "one:" + name,)})
        second = Operations("two", provided={"town_size": (lambda name: "two:" + name,)})
        assembly = build(self.town(), operations=[first, second])
        self.assertEqual(assembly.points["town_size"]("rome"), ["one:rome", "two:rome"])

    def test_the_declaring_module_reaches_its_own_point_on_needs(self):
        assembly = build(self.town())
        self.assertIs(assembly.modules["town"].needs.town_size, assembly.points["town_size"])

    def test_a_reader_gets_the_point_on_needs(self):
        reader = ModuleSpec("reader", Caller, reads=("town_size",))
        assembly = build(self.town(), reader)
        self.assertIs(assembly.modules["reader"].needs.town_size, assembly.points["town_size"])

    def test_providing_to_an_unknown_point_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", provided={"nowhere": (lambda: 1,)})])



class Gates(Module):
    def wall(self, node_id):
        return "walled" if node_id == "keep" else None

    def moat(self, node_id):
        return "moated" if node_id == "moat" else None


class Asker(Module):
    def ask(self, node_id):
        return self.needs.gate_checks(node_id)


GATES = ModuleSpec("gates", Gates, provides=(Provision("gate_checks", "wall", "wall"), Provision("gate_checks", "moat", "moat")))
ASKER = ModuleSpec("asker", Asker, reads=("gate_checks",), extension_points=(ExtensionPoint("gate_checks", LIST),))


class ProvisionTest(unittest.TestCase):
    def test_shipped_provisions_answer_in_spec_order_before_mod_providers(self):
        assembly = assemble([ASKER, GATES], [Operations("ana_test_k3f9", provided={"gate_checks": (lambda node_id: "mod",)})])
        self.assertEqual(assembly.modules["asker"].ask("keep"), ["walled", None, "mod"])

    def test_a_mod_withdraws_a_shipped_provision_by_its_module_and_name(self):
        assembly = assemble([ASKER, GATES], [Operations("ana_test_k3f9", withdrawn=("gates.wall",))])
        self.assertEqual(assembly.modules["asker"].ask("keep"), [None])

    def test_withdrawing_a_provision_nobody_makes_is_refused(self):
        with self.assertRaises(AssemblyError):
            assemble([ASKER, GATES], [Operations("ana_test_k3f9", withdrawn=("gates.drawbridge",))])

    def test_providing_to_an_undeclared_point_is_refused(self):
        with self.assertRaises(AssemblyError):
            assemble([GATES])


if __name__ == "__main__":
    unittest.main()
