"""A seat's party in an exchange takes everything from the modules that own it: the ledger's purse and cash book, the workforce's staff, the
knowledge module's techniques, the seats' stored dealings and the ventures' business. These tests set a value in each owner and read it
back through the party's ports, then check the commands the party sends and the licence the actors module grants. Over small
fixtures, no game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.actors import seat_exchange
from sim.actors.api import ALREADY_ABLE, GRANTED, NO_LICENSEE, TERMS_REFUSED, GrantLicence
from sim.actors.module import Actors
from sim.actors.seat_parties import Ports
from sim.refusal import Refusal
from sim.agents.api import Plant
from sim.seats.api import (AddLicensee, DropLapsedOffers, DropOffer, GiveShares, KeepOffer, NextOfferSerial, ReceivePatent, ReleasePatent,
                           SeatsSeat, TakeShares)
from sim.seats.module import Seats
from sim.tests import module_harness
from sim.tests.money_host import MoneyHost
from sim.ventures.api import AdoptPlant, ReleasePlant
from sim.ventures.module import Ventures
from sim.ventures.state import VenturesSeat


class PortsOverTheOwners(unittest.TestCase):
    def setUp(self):
        self.host = MoneyHost(capital=100.0)
        self.host.add_seat("second", 40.0)
        self.host.employees = {"smith": 3.0}
        self.host.known = {"fire"}

    def test_the_balance_is_the_named_seats_not_the_acting_ones(self):
        self.assertEqual((Ports(self.host, "second").balance(), Ports(self.host, "founder").balance()), (40.0, 100.0))

    def test_the_balance_is_set_for_the_named_seat_alone(self):
        Ports(self.host, "second").set_balance(75.0)
        self.assertEqual((self.host.view("seat_balance")("second"), self.host.view("seat_balance")("founder")), (75.0, 100.0))

    def test_credit_and_debit_move_the_named_seats_purse_and_cash_book(self):
        ports = Ports(self.host, "second")
        ports.credit(5.0, "sales")
        ports.debit(2.0, "toll")
        self.assertEqual((ports.balance(), self.host.slots["second"].cash_flow, self.host.slots["founder"].cash_flow),
                         (43.0, {"sales": 5.0, "toll": -2.0}, {}))

    def test_a_posting_in_the_book_is_entered_in_the_cash_book_only(self):
        ports = Ports(self.host, "second")
        ports.note_cash(1.0, 7.0, "rent")
        self.assertEqual((ports.balance(), self.host.slots["second"].cash_flow), (40.0, {"rent": 7.0}))

    def test_the_purses_are_the_actors_book(self):
        self.assertIs(Ports(self.host, "second").purses(), self.host.purses)

    def test_the_staff_and_the_know_how_are_the_owners_and_know_how_received_is_sent_as_a_command(self):
        ports = Ports(self.host, "second")
        self.assertEqual((ports.workforce(), ports.knowledge()), ({"smith": 3.0}, {"fire"}))
        ports.receive(["loom"], True)
        self.assertEqual(self.host.received, [(("loom",), True)])

    def test_the_body_of_acting_runs_as_that_seat(self):
        with Ports(self.host, "second").acting():
            self.assertEqual(self.host.state.acting_seat, "second")
        self.assertEqual(self.host.state.acting_seat, "founder")


class GrantingALicence(unittest.TestCase):
    def grant(self, licensee, problem="", granted=True, joined=("founder",), acting="founder"):
        host = MoneyHost(capital=100.0)
        module = module_harness.build(Actors, module_id="actors", world=host.world, views={
            "acting_seat": acting, "seat_list": {"joined": list(joined)}, "seat_dealings": lambda seat_id: {}})
        module.cast = lambda: SimpleNamespace(get=lambda identity: licensee if identity == "firm:a" else None)
        module.actor_world = lambda: "world"
        with mock.patch.object(seat_exchange.licence, "terms_problem", lambda *arguments: problem), \
                mock.patch.object(seat_exchange.licence, "grant", lambda *arguments: granted):
            return module.grant_licence(GrantLicence("firm:a" if licensee else "seat:b", "x", 10.0, 0.0))

    def test_a_firm_that_can_pay_is_granted_the_licence(self):
        self.assertEqual(self.grant(SimpleNamespace(kind="firm")), {"status": GRANTED})

    def test_terms_the_licensee_cannot_take_are_refused_with_the_refusal(self):
        refusal = Refusal("fee_above_value", "no")
        self.assertEqual(self.grant(SimpleNamespace(kind="firm"), problem=refusal), {"status": TERMS_REFUSED, "problem": refusal})

    def test_a_licensee_that_can_already_make_it_is_not_granted(self):
        self.assertEqual(self.grant(SimpleNamespace(kind="firm"), granted=False), {"status": ALREADY_ABLE})

    def test_an_interest_group_or_nobody_cannot_be_licensed(self):
        self.assertEqual(self.grant(SimpleNamespace(kind="interest_group")), {"status": NO_LICENSEE})
        self.assertEqual(self.grant(None), {"status": NO_LICENSEE})

    def test_another_player_who_has_joined_is_licensed_as_a_party(self):
        self.assertEqual(self.grant(None, joined=("founder", "seat:b")), {"status": GRANTED})


class TheOwnersKeepTheirRecords(unittest.TestCase):
    def test_the_seats_module_publishes_a_copy_of_a_named_seats_stored_dealings(self):
        slots = {"founder": SeatsSeat(), "second": SeatsSeat(patents={"loom": {"granted": 1}})}
        module = module_harness.build(Seats, module_id="seats")
        module.slots = lambda: slots
        published = module.seat_dealings("second")
        published["patents"]["loom"]["granted"] = 2
        self.assertEqual(published["shares_issued"], 0.0)
        self.assertEqual(slots["second"].patents, {"loom": {"granted": 1}})

    def seats(self, **fields):
        slots = {"founder": SeatsSeat(), "second": SeatsSeat(**fields)}
        module = module_harness.build(Seats, module_id="seats")
        module.slots = lambda: slots
        return module, slots

    def test_a_patent_released_leaves_the_named_seat_and_answers_the_right(self):
        module, slots = self.seats(patents={"loom": {"granted": 1, "expires": 9, "licensees": ["firm:1", "firm:2"]}})
        entry = module.release_patent(ReleasePatent("second", "loom", "firm:1"))
        self.assertEqual((entry["licensees"], slots["second"].patents), (["firm:2"], {}))

    def test_a_patent_received_is_held_as_a_copy(self):
        module, slots = self.seats()
        entry = {"granted": 1, "expires": 9, "licensees": []}
        module.receive_patent(ReceivePatent("second", "loom", entry))
        entry["expires"] = 99
        self.assertEqual((slots["second"].patents["loom"]["expires"], slots["founder"].patents), (9, {}))

    def test_a_licensee_is_added_once(self):
        module, slots = self.seats(patents={"loom": {"granted": 1, "expires": 9, "licensees": []}})
        module.add_licensee(AddLicensee("second", "loom", "firm:1"))
        module.add_licensee(AddLicensee("second", "loom", "firm:1"))
        self.assertEqual(slots["second"].patents["loom"]["licensees"], ["firm:1"])

    def test_shares_given_and_taken_move_the_held_and_issued_figures(self):
        module, slots = self.seats(shares_held={"firm:1": 0.3})
        module.give_shares(GiveShares("second", "firm:1", 0.1, False))
        module.give_shares(GiveShares("second", "second", 0.2, True))
        module.take_shares(TakeShares("second", "firm:2", 0.4, False))
        module.take_shares(TakeShares("second", "second", 0.05, True))
        seat = slots["second"]
        self.assertEqual((round(seat.shares_issued, 9), {issuer: round(share, 9) for issuer, share in seat.shares_held.items()}),
                         (0.15, {"firm:1": 0.2, "firm:2": 0.4}))

    def test_an_offer_is_kept_dropped_and_lapses(self):
        module, slots = self.seats()
        module.keep_offer(KeepOffer("second", {"id": "a#1", "expires": 100}))
        module.keep_offer(KeepOffer("second", {"id": "b#1", "expires": 120}))
        module.keep_offer(KeepOffer("second", {"id": "c#1", "expires": 130}))
        module.drop_offer(DropOffer("second", "c#1"))
        lapsed = module.drop_lapsed_offers(DropLapsedOffers("second", 110))
        self.assertEqual((lapsed, [offer["id"] for offer in slots["second"].offers]), (["a#1"], ["b#1"]))

    def test_the_offer_count_rises_by_one_and_is_answered(self):
        module, slots = self.seats(offer_serial=4)
        self.assertEqual((module.next_offer_serial(NextOfferSerial("second")), slots["second"].offer_serial), (5, 5))

    def test_a_dealing_read_after_another_partys_write_is_the_new_figure(self):
        module, _slots = self.seats()
        before = module.seat_dealings("second")
        module.keep_offer(KeepOffer("second", {"id": "a#1", "expires": 100}))
        self.assertEqual((before["offers"], module.seat_dealings("second")["offers"]), ([], [{"id": "a#1", "expires": 100}]))

    def ventures(self):
        seats = {"founder": VenturesSeat(), "second": VenturesSeat()}
        module = module_harness.build(Ventures, module_id="ventures", seat=seats["founder"])
        module.seat_slot_of = lambda seat_id: seats[seat_id]
        return module, seats

    def test_a_released_plant_leaves_the_named_seats_business_dated_when_it_had_no_year(self):
        module, seats = self.ventures()
        seats["second"].business.lifecycle.open_plant("mill", None)
        plant = module.apply_release_plant(ReleasePlant("second", "mill", 140))
        self.assertEqual((plant.entry_key, plant.opened_year, set(seats["second"].business.operating())), ("mill", 140, set()))

    def test_releasing_a_plant_the_seat_does_not_run_answers_none(self):
        module, _seats = self.ventures()
        self.assertIsNone(module.apply_release_plant(ReleasePlant("second", "mill", 140)))

    def test_an_adopted_plant_joins_the_named_seats_business_with_its_size_and_age(self):
        module, seats = self.ventures()
        plant = Plant(entry_key="mill", opened_year=90, size=3.0)
        module.apply_adopt_plant(AdoptPlant("second", plant))
        self.assertEqual((set(seats["second"].business.operating()), seats["second"].business.reading.size_of("mill"),
                          seats["second"].business.reading.opened_year_of("mill", 0)), ({"mill"}, 3.0, 90))
        self.assertEqual(set(seats["founder"].business.operating()), set())


if __name__ == "__main__":
    unittest.main()
