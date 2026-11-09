"""What `goods_year_kernel.decide_markets` reads about each offer of a batch, gathered from the year arrays in one kernel call
(`goods_table_clear.decide_reservations` used about twenty numpy calls per good for it).

A seller that is a producer of the good's recipe has a unit cost, an input share, an expected price, workshops and expected
sales; any other seller (a household or a trader) has none of them. A tile's band multiple is read from a table filled as tiles
are first asked (NaN: not yet); a tile not in it is reported in the last value so the caller can ask for it and call again."""
import numpy

from sim.jit import njit


@njit
def decide_inputs(offer_rows, offer_ptr, offers, producer_row_of_agent, recipe_row, workshops_of_producer, expected_sales_of_producer,
                  yield_factor, slot_of, good_column, cost, input_share, expected, outputs, band_multiple_of_tile, spoilage):
    """(reservation, quantity, is_producer, unit_cost, input_share, expected_price, workshops, is_multiple_workshop, expected_sales,
    band_multiple, spoilage_of_market, missing_tile) for the batch's offers (`offer_rows`, cut by market with `offer_ptr`).
    `missing_tile` is a tile id whose band multiple is NaN in `band_multiple_of_tile` (-1: none)."""
    count = len(offer_rows)
    reservation = numpy.empty(count)
    quantity = numpy.empty(count)
    is_producer = numpy.zeros(count, dtype=numpy.bool_)
    unit_cost = numpy.empty(count)
    share = numpy.zeros(count)
    expected_price = numpy.empty(count)
    workshops = numpy.ones(count)
    multiple_workshops = numpy.zeros(count, dtype=numpy.bool_)
    expected_sales = numpy.zeros(count)
    band = numpy.empty(count)
    missing_tile = -1
    for place in range(count):
        row = offer_rows[place]
        reservation[place] = offers.reservation_price[row]
        quantity[place] = offers.quantity[row]
        band[place] = band_multiple_of_tile[offers.tile[row]]
        if numpy.isnan(band[place]):
            missing_tile = offers.tile[row]
        unit_cost[place] = numpy.inf
        expected_price[place] = numpy.nan
        producer = producer_row_of_agent[offers.seller[row]]
        if producer < 0:
            continue
        is_producer[place] = True
        recipe = recipe_row[producer]
        slot = slot_of[recipe, good_column]
        workshops[place] = float(workshops_of_producer[producer])
        multiple_workshops[place] = workshops[place] > 1.0
        expected_sales[place] = expected_sales_of_producer[producer] * yield_factor[producer] * outputs[recipe, good_column]
        if slot >= 0:
            unit_cost[place] = cost[producer, slot]
            share[place] = input_share[producer, slot]
            expected_price[place] = expected[producer, slot]
    return (reservation, quantity, is_producer, unit_cost, share, expected_price, workshops, multiple_workshops, expected_sales, band,
            numpy.full(len(offer_ptr) - 1, spoilage), missing_tile)
