"""What running works draw from the market is counted per seat: a seat's reset clears only its own count, a draw is the asking
seat's, and what a seat reads back is its own. Called on `GoodsMarket` over a stand-in game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.markets.goods_market import GoodsMarket


def market_for(seats):
	"""A goods market whose asking seat is `seats[0]` until `state.acting_seat` is set again."""
	flows = {"year": 1, "drawn": {}}
	game = SimpleNamespace(market_flows=lambda: flows, state=SimpleNamespace(acting_seat=seats[0]))
	return game, GoodsMarket(game)


class DrawsBySeat(unittest.TestCase):
	def test_each_seat_reads_its_own_draw(self):
		game, market = market_for(["a", "b"])
		market.note_draw("iron", 3.0)
		game.state.acting_seat = "b"
		market.note_draw("iron", 5.0)
		self.assertEqual(market.drawn_tonnes("iron"), 5.0)
		game.state.acting_seat = "a"
		self.assertEqual(market.drawn_tonnes("iron"), 3.0)
		self.assertEqual(market.drawn_tonnes("iron", seat_id="b"), 5.0)

	def test_a_seats_reset_leaves_the_other_seats_draws(self):
		game, market = market_for(["a", "b"])
		market.note_draw("iron", 3.0)
		game.state.acting_seat = "b"
		market.note_draw("iron", 5.0)
		market.reset_draws()
		self.assertEqual(market.drawn_tonnes("iron"), 0.0)
		self.assertEqual(market.drawn_tonnes("iron", seat_id="a"), 3.0)

	def test_a_seat_renamed_keeps_its_draws_under_the_new_id(self):
		game, market = market_for(["a", "b"])
		market.note_draw("iron", 3.0)
		market.rename_draws("a", "c")
		self.assertEqual(market.drawn_tonnes("iron", seat_id="c"), 3.0)
		self.assertEqual(market.drawn_tonnes("iron", seat_id="a"), 0.0)

	def test_a_draw_that_is_not_positive_is_not_noted(self):
		_game, market = market_for(["a"])
		market.note_draw("iron", 0.0)
		self.assertEqual(market.drawn_tonnes("iron"), 0.0)


if __name__ == "__main__":
	unittest.main()
