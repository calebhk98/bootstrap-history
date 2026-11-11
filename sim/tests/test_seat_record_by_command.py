"""Complaint 931: a seat's party in an exchange holds no record of the seat's dealings or plants. What it reads is a copy from the owner, and what
the exchange changes in it is sent back to the owner as the figure the deal left (a patent moved, a share bought, an offer kept, a plant handed over).
Each function is called on plain stand-ins for the ports."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.household_party import HouseholdParty, SeatRecord
from sim.actors.seat_parties import Ports
from sim.seats.api import SeatsSeat
from sim.seats.dealings import Dealings
from sim.seats.module import Seats
from sim.seats.module_spec import MODULE_SPECS as SEATS_SPECS
from sim.tests import module_harness


def seats_over(slots):
    """A `Ports` factory for seats whose commands the seats module applies to `slots` and whose dealings it publishes."""
    module = module_harness.build(Seats, module_id="seats")
    module.slots = lambda: slots
    applies = {command_type: getattr(module, method) for command_type, method in SEATS_SPECS[0].applies if hasattr(Dealings, method)}
    needs = SimpleNamespace(send=lambda command: applies[type(command)](command), seat_dealings=_Keyed(module.seat_dealings))
    return lambda seat_id: Ports(SimpleNamespace(needs=needs), seat_id)


class _Keyed:
    def __init__(self, answer):
        self._answer = answer

    def __getitem__(self, key):
        return self._answer(key)


class TheSeatRecord(unittest.TestCase):
    def record(self, **stored):
        slots = {"second": SeatsSeat(**stored)}
        record = SeatRecord(kind="household")
        record.ports = seats_over(slots)("second")
        return record, slots["second"]

    def test_a_patent_received_is_held_by_the_seats_module(self):
        record, seat = self.record()
        record.receive_patent("loom", {"expires": 120, "licensees": []})
        self.assertEqual((seat.patents, record.patents), ({"loom": {"expires": 120, "licensees": []}}, {"loom": {"expires": 120, "licensees": []}}))

    def test_a_licensee_added_is_held_with_the_right(self):
        record, seat = self.record(patents={"loom": {"expires": 120, "licensees": []}})
        record.add_licensee("loom", "firm:1")
        self.assertEqual(seat.patents["loom"]["licensees"], ["firm:1"])

    def test_a_patent_released_leaves_the_seat(self):
        record, seat = self.record(patents={"loom": {"expires": 120, "licensees": ["firm:1"]}})
        entry = record.release_patent("loom", "firm:1")
        self.assertEqual((entry, seat.patents), ({"expires": 120, "licensees": []}, {}))

    def test_shares_taken_are_held_and_equity_given_is_issued(self):
        record, seat = self.record(shares_held={"firm:1": 0.2})
        record.take_shares("firm:2", 0.125, False)
        record.give_shares("second", 0.25, True)
        self.assertEqual((seat.shares_held, seat.shares_issued, record.issued), ({"firm:1": 0.2, "firm:2": 0.125}, 0.25, 0.25))

    def test_an_offer_kept_is_read_back_and_the_serial_counts(self):
        record, seat = self.record(offer_serial=2)
        record.keep_offer({"id": "offer:1", "expires": 100})
        self.assertEqual((record.next_offer_serial(), seat.offers, record.offers),
                         (3, [{"id": "offer:1", "expires": 100}], [{"id": "offer:1", "expires": 100}]))

    def test_a_read_is_a_copy_that_changes_nothing_when_changed(self):
        record, seat = self.record(patents={"loom": {"expires": 120, "licensees": []}})
        record.patents["loom"]["licensees"].append("firm:1")
        self.assertEqual(seat.patents["loom"]["licensees"], [])

    def test_assigning_a_dealing_is_refused(self):
        record, _seat = self.record()
        with self.assertRaises(AttributeError):
            record.issued = 1.0

    def test_two_records_for_one_seat_agree_after_either_writes(self):
        slots = {"second": SeatsSeat()}
        ports_of = seats_over(slots)
        first, second = SeatRecord(kind="household"), SeatRecord(kind="household")
        first.ports, second.ports = ports_of("second"), ports_of("second")
        held_before = second.shares_held
        first.take_shares("firm:1", 0.25, False)
        second.take_shares("firm:1", 0.125, False)
        self.assertEqual((held_before, first.shares_held, second.shares_held, slots["second"].shares_held),
                         ({}, {"firm:1": 0.375}, {"firm:1": 0.375}, {"firm:1": 0.375}))

    def test_a_record_with_no_ports_reads_empty_and_stores_nothing(self):
        record = SeatRecord(kind="household")
        record.issued = 1.0
        self.assertEqual((record.patents, record.shares_held, record.offers, record.issued), ({}, {}, [], 0.0))


class ThePartysPlants(unittest.TestCase):
    def party(self, plant):
        calls = []

        class Asked(SimpleNamespace):
            def acting(self):
                import contextlib
                return contextlib.nullcontext()

            def release_plant(self, node_id, year):
                calls.append(("release", node_id, year))
                return plant

            def adopt_plant(self, adopted):
                calls.append(("adopt", adopted))

        return HouseholdParty("founder", Asked(stored={})), calls

    def test_releasing_a_plant_asks_the_owner_with_the_year(self):
        party, calls = self.party("the plant")
        self.assertEqual((party.holdings.release_plant("mill", SimpleNamespace(setting=SimpleNamespace(year=140))), calls), ("the plant", [("release", "mill", 140)]))

    def test_releasing_a_plant_the_seat_does_not_run_is_an_error(self):
        party, _calls = self.party(None)
        with self.assertRaises(KeyError):
            party.holdings.release_plant("mill", SimpleNamespace(setting=SimpleNamespace(year=140)))

    def test_receiving_a_plant_hands_it_to_the_owner(self):
        party, calls = self.party(None)
        party.holdings.receive_plant("the plant", SimpleNamespace(year=140))
        self.assertEqual(calls, [("adopt", "the plant")])


class ThePortsSendTheOwnersCommands(unittest.TestCase):
    def test_a_dealing_and_a_plant_move_are_the_owners_commands(self):
        sent = []
        needs = SimpleNamespace(send=lambda command: sent.append(command) or "answer")
        ports = Ports(SimpleNamespace(needs=needs), "second")
        ports.keep_offer({"id": "offer:1"})
        answer = ports.release_plant("mill", 140)
        ports.adopt_plant("plant")
        self.assertEqual([(type(command).__name__, tuple(vars(command).values())) for command in sent],
                         [("KeepOffer", ("second", {"id": "offer:1"})), ("ReleasePlant", ("second", "mill", 140)), ("AdoptPlant", ("second", "plant"))])
        self.assertEqual(answer, "answer")


if __name__ == "__main__":
    unittest.main()
