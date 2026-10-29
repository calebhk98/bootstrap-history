"""Complaint 931: a seat's party in an exchange holds no record of the seat's dealings or plants. What it reads is a copy from the owner, and what
the exchange changes in it is sent back to the owner as the figure the deal left (a patent moved, a share bought, an offer kept, a plant handed over).
Each function is called on plain stand-ins for the ports."""
QUICK_TOPIC = True

import copy
import unittest
from types import SimpleNamespace

from sim.agents.household_party import HouseholdParty, SeatRecord
from sim.agents.tracked import plain, tracked
from sim.actors.seat_parties import Ports


class Sent:
    """Reports what a tracked figure tells its owner."""

    def __init__(self):
        self.figures = []

    def __call__(self):
        self.figures.append("changed")


class TrackedFigures(unittest.TestCase):
    def test_a_change_deep_inside_is_reported(self):
        told = Sent()
        patents = tracked({"loom": {"licensees": ["a"]}}, told)
        patents["loom"]["licensees"].append("b")
        self.assertEqual((told.figures, plain(patents)), (["changed"], {"loom": {"licensees": ["a", "b"]}}))

    def test_the_copy_does_not_share_with_what_it_was_made_from(self):
        stored = {"loom": {"licensees": ["a"]}}
        patents = tracked(stored, Sent())
        patents["loom"]["licensees"].append("b")
        self.assertEqual(stored, {"loom": {"licensees": ["a"]}})

    def test_a_value_taken_out_is_plain_and_changing_it_reports_nothing(self):
        told = Sent()
        patents = tracked({"loom": {"licensees": ["a"]}}, told)
        entry = patents.pop("loom")
        entry["licensees"].append("b")
        self.assertEqual((told.figures, type(entry), type(entry["licensees"])), (["changed"], dict, list))

    def test_a_deep_copy_is_plain_and_reports_nothing(self):
        told = Sent()
        offers = tracked([{"id": 1}], told)
        copied = copy.deepcopy(offers)
        copied.append({"id": 2})
        self.assertEqual((told.figures, type(copied)), ([], list))


class OwnerPorts(SimpleNamespace):
    """The owner's figures by field; `store_dealing` keeps what it is sent, as the seats module does."""

    def dealing(self, field):
        return plain(self.stored[field])

    def store_dealing(self, field, value):
        self.stored[field] = plain(value)
        self.sent.append((field, plain(value)))


def ports_holding(**stored):
    figures = dict(patents={}, shares_held={}, shares_issued=0.0, offers=[], offer_serial=0)
    figures.update(stored)
    return OwnerPorts(stored=figures, sent=[])


class TheSeatRecord(unittest.TestCase):
    def record(self, ports):
        record = SeatRecord(kind="household")
        record.ports = ports
        return record

    def test_a_patent_set_on_the_record_is_sent_to_the_owner(self):
        ports = ports_holding()
        self.record(ports).patents["loom"] = {"expires": 120, "licensees": []}
        self.assertEqual(ports.sent, [("patents", {"loom": {"expires": 120, "licensees": []}})])

    def test_a_licensee_added_inside_a_patent_is_sent_with_the_whole_figure(self):
        ports = ports_holding(patents={"loom": {"expires": 120, "licensees": []}})
        self.record(ports).patents["loom"]["licensees"].append("firm:1")
        self.assertEqual(ports.sent, [("patents", {"loom": {"expires": 120, "licensees": ["firm:1"]}})])

    def test_shares_held_are_the_records_holdings(self):
        ports = ports_holding(shares_held={"firm:1": 0.2})
        record = self.record(ports)
        record.holdings["firm:2"] = 0.1
        self.assertEqual((ports.sent, record.holdings), ([("shares_held", {"firm:1": 0.2, "firm:2": 0.1})], {"firm:1": 0.2, "firm:2": 0.1}))

    def test_equity_issued_and_the_offer_count_are_sent_when_set(self):
        ports = ports_holding()
        record = self.record(ports)
        record.issued = 0.25
        record.offer_serial = 3
        self.assertEqual((ports.sent, record.issued, record.offer_serial), ([("shares_issued", 0.25), ("offer_serial", 3)], 0.25, 3))

    def test_an_offer_appended_is_sent_and_a_later_read_sees_it(self):
        ports = ports_holding()
        record = self.record(ports)
        record.offers.append({"id": "offer:1"})
        self.assertEqual((ports.sent, record.offers), ([("offers", [{"id": "offer:1"}])], [{"id": "offer:1"}]))

    def test_a_read_after_the_owner_changed_sees_the_owners_figure(self):
        ports = ports_holding()
        record = self.record(ports)
        ports.stored["patents"] = {"loom": {}}
        self.assertEqual(record.patents, {"loom": {}})

    def test_a_record_with_no_ports_stores_nothing(self):
        record = SeatRecord(kind="household")
        record.issued = 1.0
        self.assertEqual((record.patents, record.holdings, record.offers, record.issued), ({}, {}, [], 0.0))


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
        self.assertEqual((party.release_plant("mill", SimpleNamespace(year=140)), calls), ("the plant", [("release", "mill", 140)]))

    def test_releasing_a_plant_the_seat_does_not_run_is_an_error(self):
        party, _calls = self.party(None)
        with self.assertRaises(KeyError):
            party.release_plant("mill", SimpleNamespace(year=140))

    def test_receiving_a_plant_hands_it_to_the_owner(self):
        party, calls = self.party(None)
        party.receive_plant("the plant", SimpleNamespace(year=140))
        self.assertEqual(calls, [("adopt", "the plant")])


class ThePortsSendTheOwnersCommands(unittest.TestCase):
    def test_a_stored_dealing_and_a_plant_move_are_the_owners_commands(self):
        sent = []
        needs = SimpleNamespace(send=lambda command: sent.append(command) or "answer")
        ports = Ports(SimpleNamespace(needs=needs), "second")
        ports.store_dealing("offers", [])
        answer = ports.release_plant("mill", 140)
        ports.adopt_plant("plant")
        self.assertEqual([(type(command).__name__, tuple(vars(command).values())) for command in sent],
                         [("SetDealing", ("second", "offers", [])), ("ReleasePlant", ("second", "mill", 140)), ("AdoptPlant", ("second", "plant"))])
        self.assertEqual(answer, "answer")


if __name__ == "__main__":
    unittest.main()
