"""`Applying.move_goods`, the markets module's handler of `MoveGoods`: the book of the agent economy is given one move from the
command's giver to its receiver. Called on a stand-in module whose book records the moves it is given."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.markets.api import MoveGoods
from sim.markets.commands_applied import Applying


class RecordingBook:
	def __init__(self):
		self.moves = []

	def move_many(self, moves):
		self.moves.extend(moves)


class MoveGoodsTests(unittest.TestCase):
	def test_the_book_is_given_the_commands_move(self):
		book = RecordingBook()
		module = SimpleNamespace(economy=SimpleNamespace(agent=SimpleNamespace(economy=lambda: SimpleNamespace(record=SimpleNamespace(book=book)))))
		Applying.move_goods(module, MoveGoods("edge:production", "account", "grain", "tile_a", 5.0, "mod x: a gift"))
		(move,) = book.moves
		self.assertEqual((move.giver, move.receiver, move.good, move.tile, move.quantity, move.purpose),
		                 ("edge:production", "account", "grain", "tile_a", 5.0, "mod x: a gift"))


if __name__ == "__main__":
	unittest.main()
