"""Joining a seat (`join_seat`): the seats module asks the assembly to add the seat to the registry, then sets up what is its own and its
neighbours' with the commands each owner applies, in the order a seat has always been set up. One handler over written-out views; the
registry itself (`AddSeat`) is the root's and is tested in test_assembly_root_commands."""

QUICK_TOPIC = True

import contextlib
import types
import unittest

from sim.assembly.api import AddSeat
from sim.ledger.api import OpenPurse
from sim.projects.api import WatchActive
from sim.refusal import Refusal
from sim.seats.commands import JoinSeat, SetSeatHolder
from sim.seats.module import Seats
from sim.seats.state import COUNTRY_SEAT, SeatsSeat
from sim.tests import module_harness
from sim.ventures.api import WatchBusiness
from sim.workforce.api import WatchStaff


def seats_joining(slots, answers=None):
    """The seats module over a registry of `slots` (the seat's slot for each id), acting as a seat named in `acted_as` while the
    commands inside `with act_as` are sent."""
    module = module_harness.build(
        Seats, module_id="seats", seat=SeatsSeat(), answers=answers,
        views={"tree_nodes": {}, "price_index": 1.0, "kit_capital": lambda kit: 10.0,
               "founder_life_terms": {"immortal": True, "minimum": 1.0, "mean": 1.0, "spread": 0.0},
               "game_random": types.SimpleNamespace(gauss=lambda mean, spread: mean), "civilisation": {"id": "rome"},
               "state_treasury": types.SimpleNamespace(actor_id="government:han"), "registered_seats": list(slots),
               "act_as": lambda seat_id: contextlib.nullcontext()})
    module.seat_slot_of = slots.__getitem__
    module.governed_countries = lambda: ["rome", "han"]
    return module


class JoinSeatSequence(unittest.TestCase):
    def test_a_household_seat_is_added_then_funded_given_its_years_and_watched(self):
        slots = {"second": SeatsSeat()}
        module = seats_joining(slots)
        answer = module.join_seat(JoinSeat("second", {"capital": 250.0}))
        self.assertIsNone(answer)
        self.assertEqual(module_harness.sent(module), [AddSeat("second", {"capital": 250.0}), OpenPurse("second", 250.0),
                                                       WatchBusiness("second"), WatchActive("second"), WatchStaff("second")])
        self.assertEqual(slots["second"].life_left, 1e9)

    def test_a_country_seat_holds_nothing_of_its_own_and_takes_its_governments_actor_as_holder(self):
        module = seats_joining({"han": SeatsSeat(kind=COUNTRY_SEAT)})
        answer = module.join_seat(JoinSeat("han", {"kind": COUNTRY_SEAT, "country": "han"}))
        self.assertIsNone(answer)
        sent = module_harness.sent(module)
        self.assertFalse(any(isinstance(command, OpenPurse) for command in sent))
        self.assertEqual(sent[-1], SetSeatHolder("government:han"))

    def test_a_seat_the_registry_refuses_is_refused_with_nothing_set_up(self):
        refusal = Refusal("seat_exists", "seat 'second' already exists", seat="second")
        module = seats_joining({"second": SeatsSeat()}, answers={AddSeat: refusal})
        self.assertIs(module.join_seat(JoinSeat("second", {"capital": 250.0})), refusal)
        self.assertEqual(module_harness.sent(module), [AddSeat("second", {"capital": 250.0})])


if __name__ == "__main__":
    unittest.main()
