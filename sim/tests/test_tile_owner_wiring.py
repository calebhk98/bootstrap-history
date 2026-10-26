"""Complaint 483: who owns a tile changes only through `transfer_tile`, and the colonies use it: founding a colony hands the tile
to the founding seat at the settlement level, a colony that dies out releases it. Each method is called on a stand-in `self`
carrying what it reads. The rules (the one-owner map, control levels, way owners) are test_tile_owners; the colony rules are
test_colony_rules."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.demography.api import SendSettlers
from sim.engine import colonies, tile_ownership
from sim.engine.colonies import ColoniesMixin
from sim.engine.tile_ownership import TileOwnershipMixin
from sim.geography.api import tile_owners
from sim.tests import event_stand_in


class ControlStore:
    def __init__(self):
        self.levels = {}

    def set(self, tile, level):
        if level is None:
            self.levels.pop(tile, None)
        else:
            self.levels[tile] = level

    def get(self, tile):
        return self.levels.get(tile)


class Ownership(TileOwnershipMixin):
    """The parts of a Sim that the owner map and its control store live in."""

    def __init__(self):
        self.controls = ControlStore()
        self.state = SimpleNamespace(economy=SimpleNamespace(tile_owners={"t1": {"owner": "home"}, "t2": {"owner": "home"}}))
        self.stores = SimpleNamespace(view=lambda _name: self.controls)
        self.world_map = None
        self.actors = None
        self.sent = []

    def send(self, command):
        self.sent.append(command)


class TransferTileTests(unittest.TestCase):
    def transfer(self, game, tile, to_actor, control=None):
        previous = game.transfer_tile(tile, to_actor, control, cause="test")
        return previous, game.sent

    def test_a_transfer_returns_the_previous_owner_and_moves_the_tile_at_the_given_level(self):
        game = Ownership()
        previous, _record = self.transfer(game, "t1", "rival", "garrisoned")
        self.assertEqual(previous, "home")
        self.assertEqual(game.state.economy.tile_owners, {"t1": {"owner": "rival"}, "t2": {"owner": "home"}})
        self.assertEqual(game.controls.get("t1"), "garrisoned")

    def test_releasing_a_tile_leaves_it_unowned_and_clears_its_level(self):
        game = Ownership()
        game.state.economy.tile_owners["t1"] = {"owner": "rival"}
        game.controls.set("t1", "garrisoned")
        previous, _record = self.transfer(game, "t1", None)
        self.assertEqual(previous, "rival")
        self.assertNotIn("t1", game.state.economy.tile_owners)
        self.assertIsNone(game.controls.get("t1"))

    def test_every_transfer_is_written_to_the_world_event_log_with_its_cause_and_both_owners(self):
        game = Ownership()
        _previous, sent = self.transfer(game, "t1", "rival", "garrisoned")
        record, = sent
        self.assertEqual(record.kind, "tile_transfer")
        self.assertEqual(record.tiles, ("t1",))
        self.assertEqual(record.cause, "test")
        self.assertEqual((record.facts["from_owner"], record.facts["to_owner"], record.facts["control"]), ("home", "rival", "garrisoned"))
        self.assertEqual(record.actors, ("home", "rival"))

    def test_a_transfer_is_counted_so_memoised_tile_lists_are_rebuilt(self):
        game = Ownership()
        game.__dict__["_tile_transfers"] = 4
        self.transfer(game, "t1", "rival")
        self.assertEqual(game.__dict__["_tile_transfers"], 5)


class Colonist(ColoniesMixin):
    """The parts of a Sim that founding a colony reads and writes; `transfer_tile` records its calls."""
    def send(self, command):
        if isinstance(command, SendSettlers):
            self.population.working_age -= command.people
            return None
        return event_stand_in.send(self, command)

    def __init__(self, owner_of_tile=None, spendable=1000.0):
        self.transfers = []
        self.paid = []
        self.owner_of_tile = owner_of_tile
        self.spendable = spendable
        self.population = SimpleNamespace(working_age=500.0)
        self.state = SimpleNamespace(
            household=SimpleNamespace(log=[]), acting_seat="home", scenario=SimpleNamespace(year=100),
            holdings=SimpleNamespace(colonies=[]), seats={})

    def settlement_candidates(self, by_sea=False):
        return ["far_tile"]

    def settlement_spec(self, by_sea=False):
        return "charter", {"settlers": 20, "outfit_hours_per_settler": 100.0, "by_sea": False}

    def settlement_outfit_cost(self, spec, tile_id=None):
        return 50.0

    def tile_owner(self, tile_id):
        return self.owner_of_tile

    def spending_power(self, kind):
        return self.spendable

    def pay_edge(self, edge, money, text):
        self.paid.append(money)

    def transfer_tile(self, tile_id, to_actor, control=None, cause="transfer"):
        self.transfers.append((tile_id, to_actor, control, cause))


class FoundColonyTests(unittest.TestCase):
    def found(self, game, tile="far_tile"):
        with mock.patch.object(colonies, "money_text", return_value="money"):
            return game.found_colony(tile)

    def test_a_founded_colony_hands_its_tile_to_the_acting_seat_at_the_settlement_level(self):
        game = Colonist()
        ok, _text = self.found(game)
        self.assertTrue(ok)
        self.assertEqual(game.transfers, [("far_tile", "home", tile_owners.settlement_level(), "colony founded")])

    def test_the_colony_is_recorded_and_its_settlers_leave_the_working_age_and_the_outfit_is_paid(self):
        game = Colonist()
        self.found(game)
        self.assertEqual(game.state.holdings.colonies,
                         [{"tile": "far_tile", "founded_year": 100, "by": "charter",
                           "children": 0.0, "working_age": 20.0, "elderly": 0.0}])
        self.assertEqual(game.population.working_age, 480.0)
        self.assertEqual(game.paid, [50.0])

    def test_a_tile_someone_owns_is_refused_and_nothing_moves(self):
        game = Colonist(owner_of_tile="rival")
        ok, _text = self.found(game)
        self.assertFalse(ok)
        self.assertEqual(game.transfers, [])
        self.assertEqual(game.state.holdings.colonies, [])


class DyingColonyTests(unittest.TestCase):
    def game_with_a_colony(self):
        game = Colonist()
        colony = {"tile": "far_tile", "founded_year": 100, "by": "charter", "children": 0.0, "working_age": 0.0, "elderly": 0.0}
        seat = SimpleNamespace(holdings=SimpleNamespace(colonies=[colony]))
        game.state.seats = {"home": seat}
        game.state.household.log = []
        game._disease_burden = lambda: 1.0
        game._demography = SimpleNamespace(Population=None)
        return game, seat

    def test_a_colony_that_dies_out_is_removed_and_releases_its_tile(self):
        game, seat = self.game_with_a_colony()
        with mock.patch.object(colonies, "advance_colony", return_value=True):
            game.advance_colonies(101)
        self.assertEqual(seat.holdings.colonies, [])
        self.assertEqual(game.transfers, [("far_tile", None, None, "colony died out")])

    def test_a_colony_that_survives_keeps_its_tile(self):
        game, seat = self.game_with_a_colony()
        with mock.patch.object(colonies, "advance_colony", return_value=False):
            game.advance_colonies(101)
        self.assertEqual(len(seat.holdings.colonies), 1)
        self.assertEqual(game.transfers, [])


if __name__ == "__main__":
    unittest.main()
