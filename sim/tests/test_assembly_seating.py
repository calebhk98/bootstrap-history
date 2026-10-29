"""The assembly holds the seat registry: `act_as` binds a seat's slots and tells each module, restores the seat that was acting,
and the seat ids are a view of the assembly in joining order."""

QUICK_TOPIC = True

import dataclasses
import unittest
from types import SimpleNamespace

from sim.assembly.api import Module, ModuleSpec, assemble


@dataclasses.dataclass
class Slot:
    name: str = ""


class Remembers(Module):
    """Says what it forgot on every bind."""

    def setup(self):
        self.forgot = []

    def seat_bound(self):
        self.forgot.append((self.clock.acting_seat, self.seat.name))

    def ids(self):
        return self.needs.registered_seats()


REMEMBERS = ModuleSpec("remembers", Remembers, seat_state=Slot, reads=("registered_seats",))


def game(seat_ids=("a", "b", "c")):
    assembly = assemble([REMEMBERS])
    records = {seat_id: SimpleNamespace(modules={"remembers": Slot(seat_id)}) for seat_id in seat_ids}
    assembly.seat_records = lambda: records
    followed = []
    assembly.follow = followed.append
    assembly.rebind(seat_ids[0])
    assembly.modules["remembers"].forgot.clear()
    followed.clear()
    return assembly, records, followed


class ActAs(unittest.TestCase):
    def test_the_body_acts_on_the_seats_slot_and_the_previous_seat_returns(self):
        assembly, _records, _followed = game()
        module = assembly.modules["remembers"]
        with module.act_as("b"):
            inside = (assembly.clock.acting_seat, module.seat.name)
        self.assertEqual(inside, ("b", "b"))
        self.assertEqual((assembly.clock.acting_seat, module.seat.name), ("a", "a"))

    def test_each_module_is_told_after_the_rebind_and_after_the_return(self):
        assembly, _records, _followed = game()
        module = assembly.modules["remembers"]
        with module.act_as("b"):
            pass
        self.assertEqual(module.forgot, [("b", "b"), ("a", "a")])

    def test_acting_as_the_seat_already_acting_tells_nobody(self):
        assembly, _records, _followed = game()
        module = assembly.modules["remembers"]
        with module.act_as("a"):
            pass
        self.assertEqual(module.forgot, [])

    def test_the_previous_seat_returns_when_the_body_raises(self):
        assembly, _records, _followed = game()
        module = assembly.modules["remembers"]
        with self.assertRaises(RuntimeError):
            with module.act_as("c"):
                raise RuntimeError("boom")
        self.assertEqual(assembly.clock.acting_seat, "a")

    def test_a_seat_the_body_removed_is_not_returned_to(self):
        assembly, records, _followed = game()
        module = assembly.modules["remembers"]
        with module.act_as("b"):
            del records["a"]
        self.assertEqual((assembly.clock.acting_seat, module.forgot), ("b", [("b", "b")]))

    def test_an_unknown_seat_is_a_key_error_and_nothing_changes(self):
        assembly, _records, _followed = game()
        module = assembly.modules["remembers"]
        with self.assertRaises(KeyError):
            with module.act_as("nobody"):
                pass
        self.assertEqual((assembly.clock.acting_seat, module.forgot), ("a", []))

    def test_a_load_tells_every_module_without_changing_the_seat(self):
        from sim.assembly.api import notify_seat_bound
        assembly, _records, _followed = game()
        notify_seat_bound(assembly)
        self.assertEqual((assembly.clock.acting_seat, assembly.modules["remembers"].forgot), ("a", [("a", "a")]))

    def test_the_engine_follows_every_bind(self):
        assembly, _records, followed = game()
        with assembly.act_as("c"):
            pass
        self.assertEqual(followed, ["c", "a"])

    def test_binding_without_notifying_tells_nobody(self):
        assembly, _records, _followed = game()
        assembly.rebind("b", notify=False)
        self.assertEqual((assembly.clock.acting_seat, assembly.modules["remembers"].forgot), ("b", []))


class SeatIds(unittest.TestCase):
    def test_the_view_answers_the_registry_in_joining_order(self):
        assembly, records, _followed = game(("z", "m", "a"))
        self.assertEqual(assembly.modules["remembers"].ids(), ["z", "m", "a"])
        records["late"] = SimpleNamespace(modules={"remembers": Slot("late")})
        self.assertEqual(assembly.views["registered_seats"](), ["z", "m", "a", "late"])

    def test_the_assembly_owns_the_view(self):
        assembly, _records, _followed = game()
        self.assertEqual(assembly.provider_of("registered_seats"), "assembly")

    def test_holds_are_what_the_games_rule_says_of_the_seats_record(self):
        assembly, _records, _followed = game()
        assembly.holds_rule = lambda record: ["works"] if record.modules["remembers"].name == "b" else []
        self.assertEqual((assembly.views["seat_holds"]["b"], assembly.views["seat_holds"]["a"]), (["works"], []))


if __name__ == "__main__":
    unittest.main()
