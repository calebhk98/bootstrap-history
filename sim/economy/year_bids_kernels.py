"""The entry rules' sum over the year's bids, many markets in one call (`year_bids.YearBids` is the table they read).

The sum takes the six figure columns of the block (`bid_columns.BidColumns`), `start` (the first row of each market and the row count after
the last) and, per question asked, the market's place and the price. The arithmetic is `bid_columns.demand_at_columns` on the market's
rows, one question after another, so every answer equals the single-market call bit for bit. A place outside the block (below zero or past the last market) asks about no bids and is answered with zero.
"""
import numpy

from sim.jit import njit

from .bid_columns import demand_at_columns


@njit
def demand_at_many(floor, flexible, reference, elasticity, budget, maximum, start, place, price, price_now):
    """`demand_at_columns` of market `place[question]` at `price[question]` for bids made at `price_now[question]`, for each question. Prices
    must be above zero."""
    answers = numpy.zeros(len(place))
    for question in range(len(place)):
        market = place[question]
        if market < 0 or market + 1 >= len(start):
            continue
        first, last = start[market], start[market + 1]
        answers[question] = demand_at_columns(floor[first:last], flexible[first:last], reference[first:last], elasticity[first:last],
                                              budget[first:last], maximum[first:last], price[question], price_now[question])
    return answers
