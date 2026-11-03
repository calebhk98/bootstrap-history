"""`Applying.move_goods`, the markets module's handler of `MoveGoods`: the book of the agent economy is given one move from the
command's giver to its receiver. Called on a stand-in module whose book records the moves it is given."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.book import InsufficientGoods, NegativeAmount
from sim.markets.api import MoveGoods
from sim.markets.commands_applied import Applying
from sim.refusal import Refusal
from sim.tests import module_harness


class RecordingBook:
	def __init__(self):
		self.moves = []

	def move_many(self, moves):
		self.moves.extend(moves)


class MoveGoodsTests(unittest.TestCase):
	def test_the_book_is_given_the_commands_move(self):
		book = RecordingBook()
		economy = SimpleNamespace(agent=SimpleNamespace(economy=lambda: SimpleNamespace(record=SimpleNamespace(book=book))))
		applying = module_harness.part(Applying, siblings={"market_objects": SimpleNamespace(economy=economy)})
		applying.move_goods(MoveGoods("edge:production", "account", "grain", "tile_a", 5.0, "mod x: a gift"))
		(move,) = book.moves
		self.assertEqual((move.giver, move.receiver, move.good, move.tile, move.quantity, move.purpose),
		                 ("edge:production", "account", "grain", "tile_a", 5.0, "mod x: a gift"))

	def refused(self, error):
		class RefusingBook:
			def move_many(self, moves):
				raise error
		economy = SimpleNamespace(agent=SimpleNamespace(economy=lambda: SimpleNamespace(record=SimpleNamespace(book=RefusingBook()))))
		applying = module_harness.part(Applying, siblings={"market_objects": SimpleNamespace(economy=economy)})
		return applying.move_goods(MoveGoods("account", "edge:consumption", "grain", "tile_a", 5.0, "mod x: a fire"))

	def test_a_giver_that_holds_less_is_refused_with_a_cause_not_raised(self):
		refusal = self.refused(InsufficientGoods("account holds 1 grain on tile_a but must give 5"))
		self.assertIsInstance(refusal, Refusal)
		self.assertEqual(refusal.cause, "insufficient_goods")
		self.assertEqual((refusal.facts["giver"], refusal.facts["good"], refusal.facts["tile"], refusal.facts["quantity"]),
		                 ("account", "grain", "tile_a", 5.0))

	def test_a_negative_quantity_is_refused_with_its_own_cause(self):
		self.assertEqual(self.refused(NegativeAmount("move of -1 grain is negative")).cause, "negative_amount")


if __name__ == "__main__":
	unittest.main()
