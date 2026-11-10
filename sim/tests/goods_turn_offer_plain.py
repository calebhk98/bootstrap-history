"""The turn's offers as `TurnWorld.offer` computed them before `offer_turn`: `offer_pairs`, the shortfall and the reservations of the quick
producers, each a numpy step over gathered arrays. Reference code for the kernel's test."""
import numpy

from sim.economy.goods_turn_offers_kernel import offer_pairs
from sim.economy.year_goods_offers import offer_reservations


def offer_plain(position, agent_of, tile_of_row, tile_row, recipe_row, capacity_runs, output_ptr, output_good, output_kept, spoilage,
                good_book, expected, slot_of, stock_key, stock_quantity, stock_index, cash, running, cash_target, last_runs,
                expected_sales, pays, rate, change_share, exponent):
    agents, tiles = agent_of[position], tile_of_row[tile_row[position]]
    pair_ptr, pair_good, pair_units, pair_price, pair_spoilage, slow = offer_pairs(
        position, agents, tiles, recipe_row[position], capacity_runs[position], output_ptr, output_good, output_kept, spoilage, good_book,
        expected, slot_of, stock_key, stock_quantity, stock_index)
    counts = numpy.diff(pair_ptr)
    place = numpy.repeat(numpy.arange(len(position)), counts)
    kept = ~slow[place]
    shortfall = numpy.maximum(0.0, cash_target[position] - cash - running)
    quick = numpy.flatnonzero(~slow)
    reservation = numpy.empty(0)
    if len(quick):
        pointer = numpy.zeros(len(quick) + 1, dtype=numpy.int64)
        pointer[1:] = numpy.cumsum(counts[quick])
        rows = position[quick]
        reservation = offer_reservations(pointer, pair_price[kept], pair_spoilage[kept], pair_units[kept], shortfall[quick],
                                         capacity_runs[rows], cash_target[rows], last_runs[rows], expected_sales[rows], pays[rows],
                                         rate, change_share, exponent)
    return slow, shortfall, place[kept], pair_good[kept], pair_units[kept], reservation
