"""Mod operations on an assembly: add, replace, remove, extend, adjust, with their refusals."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import AssemblyError, Module, ModuleSpec, Operations, ViewSpec
from sim.tests.assembly_fixture import BASE, TOP, Base, SetValue, build, changed


class Replacement(Base):
    def double(self):
        return -1


class Replacement2(Base):
    def double(self):
        return -2


class Empty(Module):
    def provided(self):
        return 5


class AddLayer(Base):
    pass


class PlusOne:
    def double(self):
        return super().double() + 1


class TimesTen:
    def double(self):
        return super().double() * 10


class WithHelper:
    def helper(self):
        return 1

    def double(self):
        return super().double()


def replace_base(mod_id, implementation=Replacement):
    return Operations(mod_id, replaced={"base": changed(BASE, implementation=implementation)})


class AddTest(unittest.TestCase):
    def test_a_namespaced_module_is_added(self):
        spec = ModuleSpec("religion:temple", Empty, publishes=(ViewSpec("temple_count", "provided"),))
        assembly = build(operations=[Operations("religion", added=(spec,))])
        self.assertEqual(assembly.views["temple_count"](), 5)

    def test_a_module_without_the_mod_prefix_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("religion", added=(ModuleSpec("temple", Empty),))])

    def test_a_module_with_another_mods_prefix_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("religion", added=(ModuleSpec("other:temple", Empty),))])

    def test_adding_the_same_module_twice_is_refused(self):
        spec = ModuleSpec("religion:temple", Empty)
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("religion", added=(spec, spec))])

    def test_an_added_view_that_clashes_is_refused_naming_both(self):
        spec = ModuleSpec("religion:temple", Empty, publishes=(ViewSpec("double", "provided"),))
        with self.assertRaises(AssemblyError) as caught:
            build(operations=[Operations("religion", added=(spec,))])
        self.assertIn("religion:temple", str(caught.exception))  # presentation: names both publishers
        self.assertIn("base", str(caught.exception))


class ReplaceTest(unittest.TestCase):
    def test_replace_swaps_the_implementation(self):
        assembly = build(operations=[replace_base("one")])
        self.assertEqual(assembly.views["double"](), -1)

    def test_replace_must_provide_every_view(self):
        thin = changed(BASE, implementation=Replacement, publishes=BASE.publishes[1:])
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", replaced={"base": thin})])

    def test_replace_must_apply_every_command(self):
        thin = changed(BASE, implementation=Replacement, applies=())
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", replaced={"base": thin})])

    def test_replace_must_provide_every_extension_point(self):
        from sim.assembly.api import ExtensionPoint
        with_point = changed(BASE, extension_points=(ExtensionPoint("size"),))
        thin = changed(BASE, implementation=Replacement)
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", replaced={"base": thin})], shipped=[with_point, TOP])

    def test_replacing_a_module_that_does_not_exist_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", replaced={"nothing": changed(BASE, module_id="nothing")})])

    def test_replacement_spec_must_keep_the_module_id(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", replaced={"base": changed(BASE, module_id="renamed")})])

    def test_two_unrelated_mods_replacing_one_module_are_refused_naming_both(self):
        with self.assertRaises(AssemblyError) as caught:
            build(operations=[replace_base("one"), replace_base("two", Replacement2)])
        self.assertIn("one", str(caught.exception))  # presentation: names both mods
        self.assertIn("two", str(caught.exception))

    def test_related_mods_replacing_one_module_let_the_later_win(self):
        assembly = build(operations=[replace_base("one"), replace_base("two", Replacement2)], related=lambda first, second: True)
        self.assertEqual(assembly.views["double"](), -2)
        self.assertEqual(assembly.applied.replaced_by["base"], "two")

    def test_replace_drops_earlier_layers(self):
        layered = Operations("one", layers={"base": (PlusOne,)})
        assembly = build(operations=[layered, replace_base("two")])
        self.assertEqual(assembly.views["double"](), -1)
        self.assertEqual(assembly.applied.layers.get("base", []), [])

    def test_a_layer_added_after_a_replace_stays(self):
        layered = Operations("two", layers={"base": (PlusOne,)})
        assembly = build(operations=[replace_base("one"), layered])
        self.assertEqual(assembly.views["double"](), 0)


class RemoveTest(unittest.TestCase):
    def test_removing_a_module_nobody_reads_is_allowed(self):
        assembly = build(Empty_spec(), operations=[Operations("strip", removed=("loner",))])
        self.assertNotIn("loner", assembly.modules)
        self.assertEqual(assembly.applied.removed_by["loner"], "strip")

    def test_removal_refused_while_a_module_reads_a_view_names_remover_and_reader(self):
        with self.assertRaises(AssemblyError) as caught:
            build(operations=[Operations("strip", removed=("base",))])
        self.assertIn("strip", str(caught.exception))  # presentation: the error text names the parties
        self.assertIn("top", str(caught.exception))

    def test_removal_allowed_when_another_module_provides_the_view(self):
        stand_in = ModuleSpec("strip:base", Empty, publishes=(ViewSpec("double", "provided"),))
        stand_in_ops = Operations("strip", removed=("base",), added=(stand_in,))
        assembly = build(operations=[stand_in_ops], shipped=[changed(BASE, applies=()), TOP])
        self.assertEqual(assembly.views["derived"](), 6)

    def test_a_reader_with_an_optional_read_gets_none_after_removal(self):
        reader = ModuleSpec("reader", Empty, optional_reads=("side",))
        only_side = changed(BASE, publishes=(BASE.publishes[2],), applies=())
        assembly = build(reader, operations=[Operations("strip", removed=("base",))], shipped=[only_side])
        self.assertIsNone(assembly.modules["reader"].needs.side)

    def test_removing_a_removed_module_names_the_first_remover(self):
        with self.assertRaises(AssemblyError) as caught:
            build(Empty_spec(), operations=[Operations("one", removed=("loner",)), Operations("two", removed=("loner",))])
        self.assertIn("one", str(caught.exception))  # presentation: names the first remover

    def test_removing_a_module_that_does_not_exist_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("strip", removed=("nothing",))])

    def test_removal_drops_the_modules_layers(self):
        ops = [Operations("one", layers={"loner": (PlusOne,)}), Operations("two", removed=("loner",))]
        assembly = build(Empty_spec(), operations=ops)
        self.assertNotIn("loner", assembly.applied.layers)

    def test_removal_refused_while_a_module_sends_a_command_names_the_remover(self):
        sender = ModuleSpec("sender", Empty, sends=(SetValue,))
        no_top = [changed(BASE, publishes=())]
        with self.assertRaises(AssemblyError) as caught:
            build(sender, operations=[Operations("strip", removed=("base",))], shipped=no_top)
        self.assertIn("strip", str(caught.exception))  # presentation: the error text names the parties

    def test_providing_to_a_removed_modules_point_names_the_remover(self):
        from sim.assembly.api import ExtensionPoint
        town = ModuleSpec("town", Empty, extension_points=(ExtensionPoint("town_size"),))
        ops = [Operations("strip", removed=("town",)), Operations("giver", provided={"town_size": (lambda: 1,)})]
        with self.assertRaises(AssemblyError) as caught:
            build(town, operations=ops)
        self.assertIn("strip", str(caught.exception))  # presentation: the error text names the parties

    def test_adjusting_a_removed_modules_view_names_the_remover(self):
        lonely = ModuleSpec("lonely", Empty, publishes=(ViewSpec("temple_count", "provided"),))
        ops = [Operations("strip", removed=("lonely",)), Operations("giver", adjusters={"temple_count": ((lambda needs, value: value, ()),)})]
        with self.assertRaises(AssemblyError) as caught:
            build(lonely, operations=ops)
        self.assertIn("strip", str(caught.exception))  # presentation: the error text names the parties


def Empty_spec():
    return ModuleSpec("loner", Empty)


class ExtendTest(unittest.TestCase):
    def test_a_layer_overrides_a_method_and_super_reaches_the_shipped_one(self):
        assembly = build(operations=[Operations("one", layers={"base": (PlusOne,)})])
        self.assertEqual(assembly.views["double"](), 3)

    def test_layers_stack_in_load_order_and_super_reaches_the_layer_below(self):
        ops = [Operations("one", layers={"base": (PlusOne,)}), Operations("two", layers={"base": (TimesTen,)})]
        self.assertEqual(build(operations=ops).views["double"](), 30)

    def test_the_reverse_load_order_gives_the_reverse_stack(self):
        ops = [Operations("two", layers={"base": (TimesTen,)}), Operations("one", layers={"base": (PlusOne,)})]
        self.assertEqual(build(operations=ops).views["double"](), 21)

    def test_extending_a_module_that_does_not_exist_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", layers={"nothing": (PlusOne,)})])

    def test_extending_a_removed_module_names_the_remover(self):
        ops = [Operations("strip", removed=("loner",)), Operations("one", layers={"loner": (PlusOne,)})]
        with self.assertRaises(AssemblyError) as caught:
            build(Empty_spec(), operations=ops)
        self.assertIn("strip", str(caught.exception))  # presentation: names the remover

    def test_a_layer_overriding_a_declared_method_is_stable(self):
        assembly = build(operations=[Operations("one", layers={"base": (PlusOne,)})])
        self.assertEqual(assembly.unstable, {})

    def test_a_layer_overriding_an_undeclared_method_is_listed_unstable(self):
        assembly = build(operations=[Operations("one", layers={"base": (WithHelper,)})])
        self.assertEqual(assembly.unstable, {"base": [("one", "helper")]})

    def test_a_layer_may_extend_a_module_a_mod_added(self):
        spec = ModuleSpec("religion:temple", Empty, publishes=(ViewSpec("temple_count", "provided"),))

        class Doubled:
            def provided(self):
                return super().provided() * 2
        ops = [Operations("religion", added=(spec,)), Operations("two", layers={"religion:temple": (Doubled,)})]
        self.assertEqual(build(operations=ops).views["temple_count"](), 10)


class AdjustTest(unittest.TestCase):
    def test_adjusters_apply_in_load_order(self):
        ops = [Operations("one", adjusters={"double": ((lambda needs, value: value + 1, ()),)}),
               Operations("two", adjusters={"double": ((lambda needs, value: value * 10, ()),)})]
        self.assertEqual(build(operations=ops).views["double"](), 30)

    def test_an_adjuster_receives_its_reads_on_needs(self):
        ops = [Operations("one", adjusters={"double": ((lambda needs, value: value + needs.side(), ("side",)),)})]
        self.assertEqual(build(operations=ops).views["double"](), 102)

    def test_a_bump_of_an_adjusters_read_refreshes_the_view(self):
        ops = [Operations("one", adjusters={"double": ((lambda needs, value: value + needs.side(), ("side",)),)})]
        assembly = build(operations=ops)
        base = assembly.modules["base"]
        assembly.views["double"]()
        base.side_value = 5
        base.bump("other")
        self.assertEqual(assembly.views["double"](), 7)

    def test_a_bump_of_an_adjusters_read_refreshes_a_derived_view_above(self):
        ops = [Operations("one", adjusters={"double": ((lambda needs, value: value + needs.side(), ("side",)),)})]
        assembly = build(operations=ops)
        base = assembly.modules["base"]
        assembly.views["derived"]()
        base.side_value = 5
        base.bump("other")
        self.assertEqual(assembly.views["derived"](), 8)

    def test_an_adjuster_of_a_keyed_view_receives_the_key(self):
        ops = [Operations("one", adjusters={"keyed": ((lambda needs, value, key: value + key * 100, ()),)})]
        self.assertEqual(build(operations=ops).views["keyed"][3], 303)

    def test_an_adjuster_of_a_quote_receives_the_arguments(self):
        ops = [Operations("one", adjusters={"quote": ((lambda needs, value, extra: value * extra, ()),)})]
        self.assertEqual(build(operations=ops).views["quote"](5), 30)

    def test_adjusting_an_unpublished_view_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", adjusters={"nowhere": ((lambda needs, value: value, ()),)})])

    def test_an_adjuster_reading_an_unpublished_view_is_refused(self):
        with self.assertRaises(AssemblyError):
            build(operations=[Operations("one", adjusters={"double": ((lambda needs, value: value, ("nowhere",)),)})])

    def test_a_read_outside_the_adjusters_reads_is_not_on_its_needs(self):
        ops = [Operations("one", adjusters={"double": ((lambda needs, value: needs.side(), ()),)})]
        with self.assertRaises(AttributeError):
            build(operations=ops).views["double"]()


if __name__ == "__main__":
    unittest.main()
